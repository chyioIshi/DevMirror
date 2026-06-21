"""MongoDB db_insert/db_update side effect provider."""

import copy
from typing import Any, Protocol

from app.domain.mocks.models import (
    SideEffect,
    SideEffectContext,
    SideEffectExecutionResult,
    SideEffectType,
)
from app.helpers.side_effect_provider_validation import SideEffectProviderValidation
from app.infra.exceptions import InvalidSideEffectProviderConfigError, MongoSideEffectError
from app.infra.side_effects.connection_config import ConnectionConfig
from app.infra.side_effects.connection_registry import ConnectionRegistry


class MongoSideEffectExecutor(Protocol):
    """Protocol implemented by concrete MongoDB side effect adapters."""

    async def insert_one(
        self,
        *,
        connection: ConnectionConfig,
        collection: str,
        document: dict[str, Any],
    ) -> dict[str, Any]:
        """Inserts one rendered document and returns adapter metadata."""
        ...

    async def update_one(
        self,
        *,
        connection: ConnectionConfig,
        collection: str,
        filter_: dict[str, Any],
        update: dict[str, Any],
        upsert: bool = False,
    ) -> dict[str, Any]:
        """Updates one document and returns adapter metadata."""
        ...


class MongoSideEffectProvider:
    """Executes rendered MongoDB ``db_insert`` and ``db_update`` side effects."""

    provider = "mongo"

    def __init__(
        self,
        connection_registry: ConnectionRegistry,
        side_effect_executor: MongoSideEffectExecutor,
    ) -> None:
        """Initializes the provider with connection configs and an executor."""
        self._connection_registry = connection_registry
        self._side_effect_executor = side_effect_executor

    async def execute(
        self,
        effect: SideEffect,
        context: SideEffectContext,
    ) -> SideEffectExecutionResult:
        """Executes a rendered MongoDB side effect."""

        _ = context

        self._validate_effect(effect)
        connection = self._get_connection(effect.target)
        collection = self._collection(effect.target)
        operation = effect.type.value

        try:
            match effect.type:
                case SideEffectType.DB_INSERT:
                    return await self._execute_insert(
                        effect=effect,
                        connection=connection,
                        collection=collection,
                    )
                case SideEffectType.DB_UPDATE:
                    return await self._execute_update(
                        effect=effect,
                        connection=connection,
                        collection=collection,
                    )
        except MongoSideEffectError as exc:
            return SideEffectExecutionResult(
                provider=self.provider,
                success=False,
                details={
                    "connection": connection.name,
                    "operation": operation,
                    "collection": collection,
                },
                error=str(exc),
            )

        raise InvalidSideEffectProviderConfigError(
            "Mongo provider supports only db_insert and db_update side effects",
            details={"type": effect.type.value},
        )

    async def _execute_insert(
        self,
        *,
        effect: SideEffect,
        connection: ConnectionConfig,
        collection: str,
    ) -> SideEffectExecutionResult:
        document = self._insert_document(effect.payload_template)
        metadata = await self._side_effect_executor.insert_one(
            connection=connection,
            collection=collection,
            document=document,
        )
        return SideEffectExecutionResult(
            provider=self.provider,
            success=True,
            details={
                "connection": connection.name,
                "operation": SideEffectType.DB_INSERT.value,
                "collection": collection,
                **metadata,
            },
        )

    async def _execute_update(
        self,
        *,
        effect: SideEffect,
        connection: ConnectionConfig,
        collection: str,
    ) -> SideEffectExecutionResult:
        filter_, update = self._update_payload(effect.payload_template)
        upsert = self._upsert(effect.options)
        metadata = await self._side_effect_executor.update_one(
            connection=connection,
            collection=collection,
            filter_=filter_,
            update=update,
            upsert=upsert,
        )
        return SideEffectExecutionResult(
            provider=self.provider,
            success=True,
            details={
                "connection": connection.name,
                "operation": SideEffectType.DB_UPDATE.value,
                "collection": collection,
                **metadata,
            },
        )

    def _validate_effect(self, effect: SideEffect) -> None:
        if effect.provider != self.provider:
            raise InvalidSideEffectProviderConfigError(
                "Mongo side effect provider must match mongo",
                details={"provider": effect.provider},
            )

        if effect.type not in {SideEffectType.DB_INSERT, SideEffectType.DB_UPDATE}:
            raise InvalidSideEffectProviderConfigError(
                "Mongo provider supports only db_insert and db_update side effects",
                details={"type": effect.type.value},
            )

    def _get_connection(self, target: dict[str, Any]) -> ConnectionConfig:
        connection_name = SideEffectProviderValidation.required_string(
            target,
            "connection",
            "target.connection",
            subject="Mongo",
        )
        connection = self._connection_registry.get(connection_name)
        if connection.provider != self.provider:
            raise InvalidSideEffectProviderConfigError(
                "Mongo target.connection must reference a mongo connection",
                details={
                    "field": "target.connection",
                    "connection": connection_name,
                    "provider": connection.provider,
                },
            )
        return connection

    def _collection(self, target: dict[str, Any]) -> str:
        collection = SideEffectProviderValidation.required_string(
            target,
            "collection",
            "target.collection",
            subject="Mongo",
        )
        if "$" in collection or "\x00" in collection or collection.startswith("system."):
            raise InvalidSideEffectProviderConfigError(
                "Mongo target.collection must be a safe collection name",
                details={"field": "target.collection"},
            )
        if "." in collection:
            raise InvalidSideEffectProviderConfigError(
                "Mongo target.collection must not contain dots",
                details={"field": "target.collection"},
            )
        return collection

    def _insert_document(self, payload: Any) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise InvalidSideEffectProviderConfigError(
                "Mongo db_insert payload_template must render to a dictionary",
                details={"field": "payload_template"},
            )
        if not payload:
            raise InvalidSideEffectProviderConfigError(
                "Mongo db_insert payload_template must render to a non-empty dictionary",
                details={"field": "payload_template"},
            )
        return copy.deepcopy(payload)

    def _update_payload(self, payload: Any) -> tuple[dict[str, Any], dict[str, Any]]:
        if not isinstance(payload, dict):
            raise InvalidSideEffectProviderConfigError(
                "Mongo db_update payload_template must render to a dictionary",
                details={"field": "payload_template"},
            )

        filter_ = payload.get("filter")
        if not isinstance(filter_, dict):
            raise InvalidSideEffectProviderConfigError(
                "Mongo db_update payload_template.filter must render to a dictionary",
                details={"field": "payload_template.filter"},
            )
        if not filter_:
            raise InvalidSideEffectProviderConfigError(
                "Mongo db_update payload_template.filter must be non-empty",
                details={"field": "payload_template.filter"},
            )

        update = payload.get("update")
        if not isinstance(update, dict):
            raise InvalidSideEffectProviderConfigError(
                "Mongo db_update payload_template.update must render to a dictionary",
                details={"field": "payload_template.update"},
            )
        if not update:
            raise InvalidSideEffectProviderConfigError(
                "Mongo db_update payload_template.update must be non-empty",
                details={"field": "payload_template.update"},
            )
        if not all(isinstance(key, str) and key.startswith("$") for key in update):
            raise InvalidSideEffectProviderConfigError(
                "Mongo db_update payload_template.update must use update operators",
                details={"field": "payload_template.update"},
            )

        return copy.deepcopy(filter_), copy.deepcopy(update)

    def _upsert(self, options: dict[str, Any]) -> bool:
        value = options.get("upsert")
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        raise InvalidSideEffectProviderConfigError(
            "Mongo options.upsert must be a boolean",
            details={"field": "options.upsert"},
        )
