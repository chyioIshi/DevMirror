"""Postgres db_insert side effect provider."""

import re
from collections.abc import Sequence
from typing import Any, Protocol

from app.domain.mocks.models import (
    SideEffect,
    SideEffectContext,
    SideEffectExecutionResult,
    SideEffectType,
)
from app.helpers.side_effect_provider_validation import SideEffectProviderValidation
from app.infra.exceptions import InvalidSideEffectProviderConfigError, PostgresInsertError
from app.infra.side_effects.connection_config import ConnectionConfig
from app.infra.side_effects.connection_registry import ConnectionRegistry

_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class PostgresSideEffectExecutor(Protocol):
    """Protocol implemented by concrete Postgres insert adapters.

    The provider validates table/column identifiers and builds an INSERT
    statement with placeholders. Values are passed separately as parameters;
    arbitrary SQL execution is intentionally not part of this contract.
    """

    async def execute_insert(
        self,
        *,
        connection: ConnectionConfig,
        statement: str,
        parameters: Sequence[Any],
    ) -> dict[str, Any]:
        """Executes one parameterized INSERT and returns adapter metadata."""
        ...


class PostgresSideEffectProvider:
    """Executes rendered Postgres ``db_insert`` side effects."""

    provider = "postgres"

    def __init__(
        self,
        connection_registry: ConnectionRegistry,
        side_effect_executor: PostgresSideEffectExecutor,
    ) -> None:
        """Initializes the provider with connection configs and an executor."""
        self._connection_registry = connection_registry
        self._side_effect_executor = side_effect_executor

    async def execute(
        self,
        effect: SideEffect,
        context: SideEffectContext,
    ) -> SideEffectExecutionResult:
        """Inserts the rendered payload as one Postgres row."""

        _ = context

        self._validate_effect(effect)
        connection = self._get_connection(effect.target)
        table = self._table(effect.target)
        row = self._row(effect.payload_template)
        columns = list(row.keys())
        parameters = [row[column] for column in columns]
        statement = self._insert_statement(table=table, columns=columns)

        try:
            metadata = await self._side_effect_executor.execute_insert(
                connection=connection,
                statement=statement,
                parameters=parameters,
            )
        except PostgresInsertError as exc:
            return SideEffectExecutionResult(
                provider=self.provider,
                success=False,
                details={"connection": connection.name, "table": table, "columns": columns},
                error=str(exc),
            )

        return SideEffectExecutionResult(
            provider=self.provider,
            success=True,
            details={
                "connection": connection.name,
                "table": table,
                "columns": columns,
                **metadata,
            },
        )

    def _validate_effect(self, effect: SideEffect) -> None:
        if effect.provider != self.provider:
            raise InvalidSideEffectProviderConfigError(
                "Postgres side effect provider must match postgres",
                details={"provider": effect.provider},
            )

        if effect.type != SideEffectType.DB_INSERT:
            raise InvalidSideEffectProviderConfigError(
                "Postgres provider supports only db_insert side effects",
                details={"type": effect.type.value},
            )

    def _get_connection(self, target: dict[str, Any]) -> ConnectionConfig:
        connection_name = SideEffectProviderValidation.required_string(
            target,
            "connection",
            "target.connection",
            subject="Postgres",
        )
        connection = self._connection_registry.get(connection_name)
        if connection.provider != self.provider:
            raise InvalidSideEffectProviderConfigError(
                "Postgres target.connection must reference a postgres connection",
                details={
                    "field": "target.connection",
                    "connection": connection_name,
                    "provider": connection.provider,
                },
            )
        return connection

    def _table(self, target: dict[str, Any]) -> str:
        table = SideEffectProviderValidation.required_string(
            target,
            "table",
            "target.table",
            subject="Postgres",
        )
        self._validate_table_identifier(table)
        return table

    def _row(self, payload: Any) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise InvalidSideEffectProviderConfigError(
                "Postgres db_insert payload_template must render to a dictionary",
                details={"field": "payload_template"},
            )
        if not payload:
            raise InvalidSideEffectProviderConfigError(
                "Postgres db_insert payload_template must render to a non-empty dictionary",
                details={"field": "payload_template"},
            )

        for column in payload:
            if not isinstance(column, str) or not self._is_identifier(column):
                raise InvalidSideEffectProviderConfigError(
                    "Postgres db_insert payload_template keys must be valid column identifiers",
                    details={"field": "payload_template"},
                )
        return payload

    def _validate_table_identifier(self, table: str) -> None:
        parts = table.split(".")
        if 1 <= len(parts) <= 2 and all(self._is_identifier(part) for part in parts):
            return

        raise InvalidSideEffectProviderConfigError(
            "Postgres target.table must be a valid table or schema.table identifier",
            details={"field": "target.table"},
        )

    def _is_identifier(self, value: str) -> bool:
        return bool(_IDENTIFIER_PATTERN.fullmatch(value))

    def _insert_statement(self, *, table: str, columns: list[str]) -> str:
        quoted_table = ".".join(self._quote_identifier(part) for part in table.split("."))
        quoted_columns = ", ".join(self._quote_identifier(column) for column in columns)
        placeholders = ", ".join(f"${index}" for index in range(1, len(columns) + 1))
        return f"INSERT INTO {quoted_table} ({quoted_columns}) VALUES ({placeholders})"

    def _quote_identifier(self, value: str) -> str:
        return f'"{value}"'
