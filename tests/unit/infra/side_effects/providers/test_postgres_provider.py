from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any

import pytest

from app.domain.mocks.models import SideEffect, SideEffectContext, SideEffectType
from app.infra.exceptions import (
    ConnectionNotFoundError,
    InvalidSideEffectProviderConfigError,
    PostgresInsertError,
)
from app.infra.side_effects import ConnectionConfig, ConnectionRegistry
from app.infra.side_effects.providers import PostgresSideEffectProvider


@dataclass(slots=True)
class InsertedRow:
    connection: ConnectionConfig
    statement: str
    parameters: list[Any]


@dataclass(slots=True)
class FakePostgresClient:
    inserted_rows: list[InsertedRow] = field(default_factory=list)
    error: PostgresInsertError | None = None

    async def execute_insert(
        self,
        *,
        connection: ConnectionConfig,
        statement: str,
        parameters: Sequence[Any],
    ) -> dict[str, Any]:
        if self.error is not None:
            raise self.error

        self.inserted_rows.append(
            InsertedRow(
                connection=connection,
                statement=statement,
                parameters=list(parameters),
            )
        )
        return {"command_tag": "INSERT 0 1"}


class TestPostgresSideEffectProvider:
    async def test_builds_parameterized_insert_with_quoted_identifiers(
        self,
        postgres_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        pg_client = FakePostgresClient()
        effect = side_effect_factory(
            type=SideEffectType.DB_INSERT,
            provider="postgres",
            target={"connection": "main-postgres", "table": "events"},
            payload_template={"entity_id": "entity-1", "status": "created"},
        )
        provider = PostgresSideEffectProvider(
            connection_registry=postgres_connection_registry,
            pg_client=pg_client,
        )

        result = await provider.execute(effect, side_effect_context)

        assert result.success is True
        assert result.details == {
            "connection": "main-postgres",
            "table": "events",
            "columns": ["entity_id", "status"],
            "command_tag": "INSERT 0 1",
        }
        assert pg_client.inserted_rows == [
            InsertedRow(
                connection=postgres_connection_registry.get("main-postgres"),
                statement='INSERT INTO "events" ("entity_id", "status") VALUES ($1, $2)',
                parameters=["entity-1", "created"],
            )
        ]
        assert "entity-1" not in pg_client.inserted_rows[0].statement
        assert "created" not in pg_client.inserted_rows[0].statement

    async def test_supports_schema_qualified_table_identifier(
        self,
        postgres_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        pg_client = FakePostgresClient()
        effect = side_effect_factory(
            type=SideEffectType.DB_INSERT,
            provider="postgres",
            target={"connection": "main-postgres", "table": "audit.events"},
        )
        provider = PostgresSideEffectProvider(
            connection_registry=postgres_connection_registry,
            pg_client=pg_client,
        )

        await provider.execute(effect, side_effect_context)

        assert pg_client.inserted_rows[0].statement == (
            'INSERT INTO "audit"."events" ("ok") VALUES ($1)'
        )

    async def test_unknown_connection_fails_clearly(
        self,
        postgres_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        effect = side_effect_factory(
            type=SideEffectType.DB_INSERT,
            provider="postgres",
            target={"connection": "missing", "table": "events"},
        )
        provider = PostgresSideEffectProvider(
            connection_registry=postgres_connection_registry,
            pg_client=FakePostgresClient(),
        )

        with pytest.raises(ConnectionNotFoundError) as exc_info:
            await provider.execute(effect, side_effect_context)

        assert exc_info.value.details == {"name": "missing"}

    async def test_rejects_missing_target_connection(
        self,
        postgres_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
    ) -> None:
        effect = SideEffect(
            type=SideEffectType.DB_INSERT,
            provider="postgres",
            target={"table": "events"},
            payload_template={"ok": True},
        )
        provider = PostgresSideEffectProvider(
            connection_registry=postgres_connection_registry,
            pg_client=FakePostgresClient(),
        )

        with pytest.raises(
            InvalidSideEffectProviderConfigError,
            match="target.connection must be configured",
        ):
            await provider.execute(effect, side_effect_context)

    async def test_rejects_missing_target_table(
        self,
        postgres_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
    ) -> None:
        effect = SideEffect(
            type=SideEffectType.DB_INSERT,
            provider="postgres",
            target={"connection": "main-postgres", "collection": "events"},
            payload_template={"ok": True},
        )
        provider = PostgresSideEffectProvider(
            connection_registry=postgres_connection_registry,
            pg_client=FakePostgresClient(),
        )

        with pytest.raises(
            InvalidSideEffectProviderConfigError,
            match="target.table must be configured",
        ):
            await provider.execute(effect, side_effect_context)

    async def test_returns_success_result_with_command_tag_metadata(
        self,
        postgres_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        effect = side_effect_factory(
            type=SideEffectType.DB_INSERT,
            provider="postgres",
            target={"connection": "main-postgres", "table": "events"},
        )
        provider = PostgresSideEffectProvider(
            connection_registry=postgres_connection_registry,
            pg_client=FakePostgresClient(),
        )

        result = await provider.execute(effect, side_effect_context)

        assert result.success is True
        assert result.details["command_tag"] == "INSERT 0 1"

    async def test_mismatched_connection_fails_clearly(
        self,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        registry = ConnectionRegistry(
            connections=[
                ConnectionConfig(
                    name="main-http",
                    provider="http",
                    settings={"dsn": "postgresql://localhost:5432/devmirror"},
                )
            ]
        )
        effect = side_effect_factory(
            type=SideEffectType.DB_INSERT,
            provider="postgres",
            target={"connection": "main-http", "table": "events"},
        )
        provider = PostgresSideEffectProvider(
            connection_registry=registry,
            pg_client=FakePostgresClient(),
        )

        with pytest.raises(
            InvalidSideEffectProviderConfigError,
            match="must reference a postgres connection",
        ):
            await provider.execute(effect, side_effect_context)

    async def test_provider_mismatch_fails_clearly(
        self,
        postgres_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
    ) -> None:
        effect = SideEffect(
            type=SideEffectType.DB_INSERT,
            provider="kafka",
            target={"connection": "main-postgres", "table": "events"},
            payload_template={"ok": True},
        )
        provider = PostgresSideEffectProvider(
            connection_registry=postgres_connection_registry,
            pg_client=FakePostgresClient(),
        )

        with pytest.raises(
            InvalidSideEffectProviderConfigError,
            match="provider must match postgres",
        ):
            await provider.execute(effect, side_effect_context)

    async def test_wrong_side_effect_type_fails_clearly(
        self,
        postgres_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
    ) -> None:
        effect = SideEffect(
            type=SideEffectType.DB_UPDATE,
            provider="postgres",
            target={"connection": "main-postgres", "table": "events"},
            payload_template={"ok": True},
        )
        provider = PostgresSideEffectProvider(
            connection_registry=postgres_connection_registry,
            pg_client=FakePostgresClient(),
        )

        with pytest.raises(
            InvalidSideEffectProviderConfigError,
            match="supports only db_insert",
        ):
            await provider.execute(effect, side_effect_context)

    async def test_rejects_invalid_table_identifier(
        self,
        postgres_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        effect = side_effect_factory(
            type=SideEffectType.DB_INSERT,
            provider="postgres",
            target={"connection": "main-postgres", "table": "events;drop table users"},
        )
        provider = PostgresSideEffectProvider(
            connection_registry=postgres_connection_registry,
            pg_client=FakePostgresClient(),
        )

        with pytest.raises(
            InvalidSideEffectProviderConfigError,
            match="target.table must be a valid table or schema.table identifier",
        ):
            await provider.execute(effect, side_effect_context)

    async def test_rejects_table_with_more_than_two_parts(
        self,
        postgres_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        effect = side_effect_factory(
            type=SideEffectType.DB_INSERT,
            provider="postgres",
            target={"connection": "main-postgres", "table": "audit.public.events"},
        )
        provider = PostgresSideEffectProvider(
            connection_registry=postgres_connection_registry,
            pg_client=FakePostgresClient(),
        )

        with pytest.raises(
            InvalidSideEffectProviderConfigError,
            match="target.table must be a valid table or schema.table identifier",
        ):
            await provider.execute(effect, side_effect_context)

    async def test_rejects_invalid_column_identifier(
        self,
        postgres_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        effect = side_effect_factory(
            type=SideEffectType.DB_INSERT,
            provider="postgres",
            target={"connection": "main-postgres", "table": "events"},
            payload_template={"entity_id;drop": "entity-1"},
        )
        provider = PostgresSideEffectProvider(
            connection_registry=postgres_connection_registry,
            pg_client=FakePostgresClient(),
        )

        with pytest.raises(
            InvalidSideEffectProviderConfigError,
            match="payload_template keys must be valid column identifiers",
        ):
            await provider.execute(effect, side_effect_context)

    async def test_rejects_non_dict_payload(
        self,
        postgres_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
    ) -> None:
        effect = SideEffect(
            type=SideEffectType.DB_INSERT,
            provider="postgres",
            target={"connection": "main-postgres", "table": "events"},
            payload_template=["not-a-row"],  # type: ignore[arg-type]
        )
        provider = PostgresSideEffectProvider(
            connection_registry=postgres_connection_registry,
            pg_client=FakePostgresClient(),
        )

        with pytest.raises(
            InvalidSideEffectProviderConfigError,
            match="payload_template must render to a dictionary",
        ):
            await provider.execute(effect, side_effect_context)

    async def test_rejects_empty_payload(
        self,
        postgres_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        effect = side_effect_factory(
            type=SideEffectType.DB_INSERT,
            provider="postgres",
            target={"connection": "main-postgres", "table": "events"},
            payload_template={},
        )
        provider = PostgresSideEffectProvider(
            connection_registry=postgres_connection_registry,
            pg_client=FakePostgresClient(),
        )

        with pytest.raises(
            InvalidSideEffectProviderConfigError,
            match="payload_template must render to a non-empty dictionary",
        ):
            await provider.execute(effect, side_effect_context)

    async def test_preserves_column_and_parameter_ordering(
        self,
        postgres_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        pg_client = FakePostgresClient()
        effect = side_effect_factory(
            type=SideEffectType.DB_INSERT,
            provider="postgres",
            target={"connection": "main-postgres", "table": "events"},
            payload_template={"first_column": 1, "second_column": 2, "third_column": 3},
        )
        provider = PostgresSideEffectProvider(
            connection_registry=postgres_connection_registry,
            pg_client=pg_client,
        )

        result = await provider.execute(effect, side_effect_context)

        assert result.details["columns"] == [
            "first_column",
            "second_column",
            "third_column",
        ]
        assert pg_client.inserted_rows[0].parameters == [1, 2, 3]

    async def test_postgres_insert_error_returns_failed_execution_result(
        self,
        postgres_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        effect = side_effect_factory(
            type=SideEffectType.DB_INSERT,
            provider="postgres",
            target={"connection": "main-postgres", "table": "events"},
        )
        provider = PostgresSideEffectProvider(
            connection_registry=postgres_connection_registry,
            pg_client=FakePostgresClient(
                error=PostgresInsertError("insert failed"),
            ),
        )

        result = await provider.execute(effect, side_effect_context)

        assert result.success is False
        assert result.details == {
            "connection": "main-postgres",
            "table": "events",
            "columns": ["ok"],
        }
        assert result.error == "insert failed"
