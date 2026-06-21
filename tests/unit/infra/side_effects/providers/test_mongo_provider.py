from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import pytest

from app.domain.mocks.models import SideEffect, SideEffectContext, SideEffectType
from app.infra.exceptions import (
    ConnectionNotFoundError,
    InvalidSideEffectProviderConfigError,
    MongoSideEffectError,
)
from app.infra.side_effects import ConnectionConfig, ConnectionRegistry
from app.infra.side_effects.providers import MongoSideEffectProvider


@dataclass(slots=True)
class MongoCall:
    operation: str
    connection: ConnectionConfig
    collection: str
    parameters: dict[str, Any]


@dataclass(slots=True)
class FakeMongoSideEffectExecutor:
    calls: list[MongoCall] = field(default_factory=list)
    error: MongoSideEffectError | None = None
    mutate_insert_document: bool = False

    async def insert_one(
        self,
        *,
        connection: ConnectionConfig,
        collection: str,
        document: dict[str, Any],
    ) -> dict[str, Any]:
        if self.error is not None:
            raise self.error
        if self.mutate_insert_document:
            document["_id"] = "driver-generated-id"
        self.calls.append(
            MongoCall(
                operation="db_insert",
                connection=connection,
                collection=collection,
                parameters={"document": document},
            )
        )
        return {"inserted_id": "document-1"}

    async def update_one(
        self,
        *,
        connection: ConnectionConfig,
        collection: str,
        filter_: dict[str, Any],
        update: dict[str, Any],
        upsert: bool = False,
    ) -> dict[str, Any]:
        if self.error is not None:
            raise self.error
        self.calls.append(
            MongoCall(
                operation="db_update",
                connection=connection,
                collection=collection,
                parameters={"filter": filter_, "update": update, "upsert": upsert},
            )
        )
        return {"matched_count": 1, "modified_count": 1, "upserted_id": None}


class TestMongoSideEffectProvider:
    async def test_inserts_document(
        self,
        mongo_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        executor = FakeMongoSideEffectExecutor()
        effect = side_effect_factory(
            type=SideEffectType.DB_INSERT,
            provider="mongo",
            target={"connection": "main-mongo", "collection": "mock_events"},
            payload_template={"event": "mock_served"},
        )
        provider = MongoSideEffectProvider(
            connection_registry=mongo_connection_registry,
            side_effect_executor=executor,
        )

        result = await provider.execute(effect, side_effect_context)

        assert result.success is True
        assert result.details == {
            "connection": "main-mongo",
            "operation": "db_insert",
            "collection": "mock_events",
            "inserted_id": "document-1",
        }
        assert executor.calls == [
            MongoCall(
                operation="db_insert",
                connection=mongo_connection_registry.get("main-mongo"),
                collection="mock_events",
                parameters={"document": {"event": "mock_served"}},
            )
        ]

    async def test_insert_does_not_mutate_original_payload(
        self,
        mongo_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        payload = {"event": "mock_served"}
        effect = side_effect_factory(
            type=SideEffectType.DB_INSERT,
            provider="mongo",
            target={"connection": "main-mongo", "collection": "mock_events"},
            payload_template=payload,
        )
        provider = MongoSideEffectProvider(
            connection_registry=mongo_connection_registry,
            side_effect_executor=FakeMongoSideEffectExecutor(mutate_insert_document=True),
        )

        await provider.execute(effect, side_effect_context)

        assert payload == {"event": "mock_served"}
        assert effect.payload_template == {"event": "mock_served"}

    async def test_updates_document_with_default_upsert_false(
        self,
        mongo_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        executor = FakeMongoSideEffectExecutor()
        effect = side_effect_factory(
            type=SideEffectType.DB_UPDATE,
            provider="mongo",
            target={"connection": "main-mongo", "collection": "mock_state"},
            payload_template={
                "filter": {"requestId": "request-1"},
                "update": {"$set": {"status": "served"}},
            },
        )
        provider = MongoSideEffectProvider(
            connection_registry=mongo_connection_registry,
            side_effect_executor=executor,
        )

        result = await provider.execute(effect, side_effect_context)

        assert result.success is True
        assert result.details == {
            "connection": "main-mongo",
            "operation": "db_update",
            "collection": "mock_state",
            "matched_count": 1,
            "modified_count": 1,
            "upserted_id": None,
        }
        assert executor.calls[0].parameters == {
            "filter": {"requestId": "request-1"},
            "update": {"$set": {"status": "served"}},
            "upsert": False,
        }

    async def test_updates_document_with_upsert_true(
        self,
        mongo_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        executor = FakeMongoSideEffectExecutor()
        effect = side_effect_factory(
            type=SideEffectType.DB_UPDATE,
            provider="mongo",
            target={"connection": "main-mongo", "collection": "mock_state"},
            payload_template={"filter": {"id": "state-1"}, "update": {"$set": {"ok": True}}},
            options={"upsert": True},
        )
        provider = MongoSideEffectProvider(
            connection_registry=mongo_connection_registry,
            side_effect_executor=executor,
        )

        await provider.execute(effect, side_effect_context)

        assert executor.calls[0].parameters["upsert"] is True

    async def test_unknown_connection_fails_clearly(
        self,
        mongo_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        effect = side_effect_factory(
            type=SideEffectType.DB_INSERT,
            provider="mongo",
            target={"connection": "missing", "collection": "mock_events"},
        )
        provider = MongoSideEffectProvider(
            connection_registry=mongo_connection_registry,
            side_effect_executor=FakeMongoSideEffectExecutor(),
        )

        with pytest.raises(ConnectionNotFoundError) as exc_info:
            await provider.execute(effect, side_effect_context)

        assert exc_info.value.details == {"name": "missing"}

    async def test_mismatched_connection_fails_clearly(
        self,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        registry = ConnectionRegistry(
            connections=[
                ConnectionConfig(
                    name="main-postgres",
                    provider="postgres",
                    settings={"dsn": "postgresql://localhost:5432/devmirror"},
                )
            ]
        )
        effect = side_effect_factory(
            type=SideEffectType.DB_INSERT,
            provider="mongo",
            target={"connection": "main-postgres", "collection": "mock_events"},
        )
        provider = MongoSideEffectProvider(
            connection_registry=registry,
            side_effect_executor=FakeMongoSideEffectExecutor(),
        )

        with pytest.raises(
            InvalidSideEffectProviderConfigError,
            match="must reference a mongo connection",
        ):
            await provider.execute(effect, side_effect_context)

    async def test_provider_mismatch_fails_clearly(
        self,
        mongo_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
    ) -> None:
        effect = SideEffect(
            type=SideEffectType.DB_INSERT,
            provider="postgres",
            target={"connection": "main-mongo", "collection": "mock_events"},
            payload_template={"ok": True},
        )
        provider = MongoSideEffectProvider(
            connection_registry=mongo_connection_registry,
            side_effect_executor=FakeMongoSideEffectExecutor(),
        )

        with pytest.raises(
            InvalidSideEffectProviderConfigError,
            match="provider must match mongo",
        ):
            await provider.execute(effect, side_effect_context)

    async def test_unsupported_type_fails_clearly(
        self,
        mongo_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
    ) -> None:
        effect = SideEffect(
            type=SideEffectType.HTTP_CALLBACK,
            provider="mongo",
            target={"connection": "main-mongo"},
            payload_template={"ok": True},
        )
        provider = MongoSideEffectProvider(
            connection_registry=mongo_connection_registry,
            side_effect_executor=FakeMongoSideEffectExecutor(),
        )

        with pytest.raises(
            InvalidSideEffectProviderConfigError,
            match="supports only db_insert and db_update",
        ):
            await provider.execute(effect, side_effect_context)

    async def test_rejects_missing_target_connection(
        self,
        mongo_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
    ) -> None:
        effect = SideEffect(
            type=SideEffectType.DB_INSERT,
            provider="mongo",
            target={"collection": "mock_events"},
            payload_template={"ok": True},
        )
        provider = MongoSideEffectProvider(
            connection_registry=mongo_connection_registry,
            side_effect_executor=FakeMongoSideEffectExecutor(),
        )

        with pytest.raises(
            InvalidSideEffectProviderConfigError,
            match="target.connection must be configured",
        ):
            await provider.execute(effect, side_effect_context)

    async def test_rejects_missing_target_collection(
        self,
        mongo_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
    ) -> None:
        effect = SideEffect(
            type=SideEffectType.DB_INSERT,
            provider="mongo",
            target={"connection": "main-mongo", "table": "mock_events"},
            payload_template={"ok": True},
        )
        provider = MongoSideEffectProvider(
            connection_registry=mongo_connection_registry,
            side_effect_executor=FakeMongoSideEffectExecutor(),
        )

        with pytest.raises(
            InvalidSideEffectProviderConfigError,
            match="target.collection must be configured",
        ):
            await provider.execute(effect, side_effect_context)

    @pytest.mark.parametrize(
        "collection",
        ["system.profile", "mock.events", "mock$events", "mock\x00events"],
    )
    async def test_rejects_invalid_collection_name(
        self,
        mongo_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
        collection: str,
    ) -> None:
        effect = side_effect_factory(
            type=SideEffectType.DB_INSERT,
            provider="mongo",
            target={"connection": "main-mongo", "collection": collection},
        )
        provider = MongoSideEffectProvider(
            connection_registry=mongo_connection_registry,
            side_effect_executor=FakeMongoSideEffectExecutor(),
        )

        with pytest.raises(InvalidSideEffectProviderConfigError):
            await provider.execute(effect, side_effect_context)

    async def test_insert_rejects_non_dict_payload(
        self,
        mongo_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
    ) -> None:
        effect = SideEffect(
            type=SideEffectType.DB_INSERT,
            provider="mongo",
            target={"connection": "main-mongo", "collection": "mock_events"},
            payload_template=["not-a-document"],  # type: ignore[arg-type]
        )
        provider = MongoSideEffectProvider(
            connection_registry=mongo_connection_registry,
            side_effect_executor=FakeMongoSideEffectExecutor(),
        )

        with pytest.raises(
            InvalidSideEffectProviderConfigError,
            match="payload_template must render to a dictionary",
        ):
            await provider.execute(effect, side_effect_context)

    async def test_insert_rejects_empty_payload(
        self,
        mongo_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        effect = side_effect_factory(
            type=SideEffectType.DB_INSERT,
            provider="mongo",
            target={"connection": "main-mongo", "collection": "mock_events"},
            payload_template={},
        )
        provider = MongoSideEffectProvider(
            connection_registry=mongo_connection_registry,
            side_effect_executor=FakeMongoSideEffectExecutor(),
        )

        with pytest.raises(
            InvalidSideEffectProviderConfigError,
            match="payload_template must render to a non-empty dictionary",
        ):
            await provider.execute(effect, side_effect_context)

    async def test_update_rejects_non_dict_payload(
        self,
        mongo_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
    ) -> None:
        effect = SideEffect(
            type=SideEffectType.DB_UPDATE,
            provider="mongo",
            target={"connection": "main-mongo", "collection": "mock_state"},
            payload_template=["not-an-update"],  # type: ignore[arg-type]
        )
        provider = MongoSideEffectProvider(
            connection_registry=mongo_connection_registry,
            side_effect_executor=FakeMongoSideEffectExecutor(),
        )

        with pytest.raises(
            InvalidSideEffectProviderConfigError,
            match="payload_template must render to a dictionary",
        ):
            await provider.execute(effect, side_effect_context)

    @pytest.mark.parametrize(
        "payload",
        [
            {},
            {"update": {"$set": {"ok": True}}},
            {"filter": [], "update": {"$set": {"ok": True}}},
            {"filter": {}, "update": {"$set": {"ok": True}}},
        ],
    )
    async def test_update_rejects_missing_or_empty_filter(
        self,
        mongo_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
        payload: dict[str, Any],
    ) -> None:
        effect = side_effect_factory(
            type=SideEffectType.DB_UPDATE,
            provider="mongo",
            target={"connection": "main-mongo", "collection": "mock_state"},
            payload_template=payload,
        )
        provider = MongoSideEffectProvider(
            connection_registry=mongo_connection_registry,
            side_effect_executor=FakeMongoSideEffectExecutor(),
        )

        with pytest.raises(InvalidSideEffectProviderConfigError, match="filter"):
            await provider.execute(effect, side_effect_context)

    @pytest.mark.parametrize(
        "payload",
        [
            {"filter": {"id": "state-1"}},
            {"filter": {"id": "state-1"}, "update": []},
            {"filter": {"id": "state-1"}, "update": {}},
        ],
    )
    async def test_update_rejects_missing_or_empty_update(
        self,
        mongo_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
        payload: dict[str, Any],
    ) -> None:
        effect = side_effect_factory(
            type=SideEffectType.DB_UPDATE,
            provider="mongo",
            target={"connection": "main-mongo", "collection": "mock_state"},
            payload_template=payload,
        )
        provider = MongoSideEffectProvider(
            connection_registry=mongo_connection_registry,
            side_effect_executor=FakeMongoSideEffectExecutor(),
        )

        with pytest.raises(InvalidSideEffectProviderConfigError, match="update"):
            await provider.execute(effect, side_effect_context)

    async def test_update_rejects_replacement_style_update(
        self,
        mongo_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        effect = side_effect_factory(
            type=SideEffectType.DB_UPDATE,
            provider="mongo",
            target={"connection": "main-mongo", "collection": "mock_state"},
            payload_template={"filter": {"id": "state-1"}, "update": {"status": "served"}},
        )
        provider = MongoSideEffectProvider(
            connection_registry=mongo_connection_registry,
            side_effect_executor=FakeMongoSideEffectExecutor(),
        )

        with pytest.raises(
            InvalidSideEffectProviderConfigError,
            match="must use update operators",
        ):
            await provider.execute(effect, side_effect_context)

    async def test_update_rejects_invalid_upsert(
        self,
        mongo_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        effect = side_effect_factory(
            type=SideEffectType.DB_UPDATE,
            provider="mongo",
            target={"connection": "main-mongo", "collection": "mock_state"},
            payload_template={"filter": {"id": "state-1"}, "update": {"$set": {"ok": True}}},
            options={"upsert": "yes"},
        )
        provider = MongoSideEffectProvider(
            connection_registry=mongo_connection_registry,
            side_effect_executor=FakeMongoSideEffectExecutor(),
        )

        with pytest.raises(InvalidSideEffectProviderConfigError, match="options.upsert"):
            await provider.execute(effect, side_effect_context)

    async def test_mongo_error_returns_failed_execution_result(
        self,
        mongo_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        effect = side_effect_factory(
            type=SideEffectType.DB_INSERT,
            provider="mongo",
            target={"connection": "main-mongo", "collection": "mock_events"},
        )
        provider = MongoSideEffectProvider(
            connection_registry=mongo_connection_registry,
            side_effect_executor=FakeMongoSideEffectExecutor(
                error=MongoSideEffectError("mongo failed")
            ),
        )

        result = await provider.execute(effect, side_effect_context)

        assert result.success is False
        assert result.details == {
            "connection": "main-mongo",
            "operation": "db_insert",
            "collection": "mock_events",
        }
        assert result.error == "mongo failed"
