import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, ClassVar

import pytest

from app.infra.exceptions import InvalidSideEffectProviderConfigError, MongoSideEffectError
from app.infra.side_effects import ConnectionConfig
from app.infra.side_effects.providers import AsyncMongoSideEffectExecutor


@dataclass(slots=True)
class InsertOneResult:
    inserted_id: Any


@dataclass(slots=True)
class UpdateOneResult:
    matched_count: int
    modified_count: int
    upserted_id: Any = None


@dataclass(slots=True)
class MongoCommand:
    name: str
    collection: str
    parameters: dict[str, Any]


@dataclass(slots=True)
class FakeMongoCollection:
    name: str
    commands: list[MongoCommand]

    async def insert_one(self, document: dict[str, Any]) -> InsertOneResult:
        if FakePymongoAsyncMongoClient.command_error is not None:
            raise FakePymongoAsyncMongoClient.command_error
        self.commands.append(
            MongoCommand(
                name="insert_one",
                collection=self.name,
                parameters={"document": document},
            )
        )
        return InsertOneResult(inserted_id="document-1")

    async def update_one(
        self,
        filter_: dict[str, Any],
        update: dict[str, Any],
        *,
        upsert: bool = False,
    ) -> UpdateOneResult:
        if FakePymongoAsyncMongoClient.command_error is not None:
            raise FakePymongoAsyncMongoClient.command_error
        self.commands.append(
            MongoCommand(
                name="update_one",
                collection=self.name,
                parameters={"filter": filter_, "update": update, "upsert": upsert},
            )
        )
        return UpdateOneResult(matched_count=1, modified_count=1, upserted_id="upserted-1")


@dataclass(slots=True)
class FakeMongoDatabase:
    commands: list[MongoCommand]

    def __getitem__(self, collection: str) -> FakeMongoCollection:
        return FakeMongoCollection(name=collection, commands=self.commands)


class FakePymongoAsyncMongoClient:
    created_clients: ClassVar[list["FakePymongoAsyncMongoClient"]] = []
    create_client_error: ClassVar[Exception | None] = None
    command_error: ClassVar[Exception | None] = None
    close_error_hosts: ClassVar[set[str]] = set()

    def __init__(self, **kwargs: Any) -> None:
        if type(self).create_client_error is not None:
            raise type(self).create_client_error
        self.kwargs = kwargs
        self.closed = False
        self.commands: list[MongoCommand] = []
        type(self).created_clients.append(self)

    def __getitem__(self, database: str) -> FakeMongoDatabase:
        return FakeMongoDatabase(commands=self.commands)

    def close(self) -> None:
        self.closed = True
        if self.kwargs["host"] in type(self).close_error_hosts:
            raise RuntimeError(f"close failed: {self.kwargs['host']}")


class TestAsyncMongoSideEffectExecutor:
    @pytest.fixture(autouse=True)
    def reset_fake_mongo(self, monkeypatch: pytest.MonkeyPatch) -> None:
        FakePymongoAsyncMongoClient.created_clients.clear()
        FakePymongoAsyncMongoClient.create_client_error = None
        FakePymongoAsyncMongoClient.command_error = None
        FakePymongoAsyncMongoClient.close_error_hosts = set()

        monkeypatch.setattr(
            "app.infra.side_effects.providers.mongo_side_effect_executor.PymongoAsyncMongoClient",
            FakePymongoAsyncMongoClient,
        )

    @pytest.fixture
    def mongo_connection(
        self,
        connection_factory: Callable[..., ConnectionConfig],
    ) -> ConnectionConfig:
        return connection_factory(
            name="main-mongo",
            provider="mongo",
            dsn=None,
            settings={"uri": "mongodb://localhost:27017", "database": "devmirror"},
        )

    async def test_insert_one_executes_command(self, mongo_connection: ConnectionConfig) -> None:
        client = AsyncMongoSideEffectExecutor()

        result = await client.insert_one(
            connection=mongo_connection,
            collection="mock_events",
            document={"event": "mock_served"},
        )

        assert result == {"inserted_id": "document-1"}
        assert FakePymongoAsyncMongoClient.created_clients[0].commands == [
            MongoCommand(
                name="insert_one",
                collection="mock_events",
                parameters={"document": {"event": "mock_served"}},
            )
        ]

    async def test_update_one_executes_command(self, mongo_connection: ConnectionConfig) -> None:
        client = AsyncMongoSideEffectExecutor()

        result = await client.update_one(
            connection=mongo_connection,
            collection="mock_state",
            filter_={"id": "state-1"},
            update={"$set": {"ok": True}},
            upsert=True,
        )

        assert result == {"matched_count": 1, "modified_count": 1, "upserted_id": "upserted-1"}
        assert FakePymongoAsyncMongoClient.created_clients[0].commands == [
            MongoCommand(
                name="update_one",
                collection="mock_state",
                parameters={
                    "filter": {"id": "state-1"},
                    "update": {"$set": {"ok": True}},
                    "upsert": True,
                },
            )
        ]

    async def test_creates_executor_once_for_same_connection_settings(
        self,
        mongo_connection: ConnectionConfig,
    ) -> None:
        client = AsyncMongoSideEffectExecutor()

        await asyncio.gather(
            *[
                client.insert_one(
                    connection=mongo_connection,
                    collection="mock_events",
                    document={"index": index},
                )
                for index in range(5)
            ]
        )

        assert len(FakePymongoAsyncMongoClient.created_clients) == 1
        assert len(FakePymongoAsyncMongoClient.created_clients[0].commands) == 5

    async def test_reuses_cached_executor(self, mongo_connection: ConnectionConfig) -> None:
        client = AsyncMongoSideEffectExecutor()

        await client.insert_one(
            connection=mongo_connection,
            collection="first_collection",
            document={"ok": True},
        )
        await client.insert_one(
            connection=mongo_connection,
            collection="second_collection",
            document={"ok": False},
        )

        assert len(FakePymongoAsyncMongoClient.created_clients) == 1
        assert [
            command.collection
            for command in FakePymongoAsyncMongoClient.created_clients[0].commands
        ] == ["first_collection", "second_collection"]

    async def test_creates_different_executors_for_different_settings(
        self,
        connection_factory: Callable[..., ConnectionConfig],
    ) -> None:
        client = AsyncMongoSideEffectExecutor()

        for connection in [
            connection_factory(
                name="first-mongo",
                provider="mongo",
                dsn=None,
                settings={"uri": "mongodb://localhost:27017", "database": "devmirror"},
            ),
            connection_factory(
                name="second-mongo",
                provider="mongo",
                dsn=None,
                settings={"uri": "mongodb://localhost:27017", "database": "devmirror"},
            ),
            connection_factory(
                name="first-mongo",
                provider="mongo",
                dsn=None,
                settings={"uri": "mongodb://localhost:27018", "database": "devmirror"},
            ),
            connection_factory(
                name="first-mongo",
                provider="mongo",
                dsn=None,
                settings={"uri": "mongodb://localhost:27017", "database": "other"},
            ),
            connection_factory(
                name="first-mongo",
                provider="mongo",
                dsn=None,
                settings={
                    "uri": "mongodb://localhost:27017",
                    "database": "devmirror",
                    "max_pool_size": 2,
                },
            ),
        ]:
            await client.insert_one(
                connection=connection,
                collection="mock_events",
                document={"ok": True},
            )

        assert len(FakePymongoAsyncMongoClient.created_clients) == 5

    async def test_passes_executor_options_to_pymongo(
        self,
        connection_factory: Callable[..., ConnectionConfig],
    ) -> None:
        client = AsyncMongoSideEffectExecutor()

        await client.insert_one(
            connection=connection_factory(
                name="main-mongo",
                provider="mongo",
                dsn=None,
                settings={
                    "uri": "mongodb://localhost:27017",
                    "database": "devmirror",
                    "server_selection_timeout_ms": 5000,
                    "max_pool_size": 5,
                    "min_pool_size": 1,
                },
            ),
            collection="mock_events",
            document={"ok": True},
        )

        assert FakePymongoAsyncMongoClient.created_clients[0].kwargs == {
            "host": "mongodb://localhost:27017",
            "serverSelectionTimeoutMS": 5000,
            "maxPoolSize": 5,
            "minPoolSize": 1,
        }

    @pytest.mark.parametrize(
        ("settings", "message"),
        [
            ({}, "connection.settings.uri must be configured"),
            (
                {"uri": "mongodb://localhost:27017"},
                "connection.settings.database must be configured",
            ),
            (
                {
                    "uri": "mongodb://localhost:27017",
                    "database": "devmirror",
                    "server_selection_timeout_ms": 0,
                },
                "connection.settings.server_selection_timeout_ms must be a positive integer",
            ),
            (
                {
                    "uri": "mongodb://localhost:27017",
                    "database": "devmirror",
                    "min_pool_size": -1,
                },
                "connection.settings.min_pool_size must be a non-negative integer",
            ),
            (
                {
                    "uri": "mongodb://localhost:27017",
                    "database": "devmirror",
                    "max_pool_size": 0,
                },
                "connection.settings.max_pool_size must be a positive integer",
            ),
            (
                {
                    "uri": "mongodb://localhost:27017",
                    "database": "devmirror",
                    "min_pool_size": 3,
                    "max_pool_size": 2,
                },
                "max_pool_size must be greater than or equal to min_pool_size",
            ),
        ],
    )
    async def test_invalid_executor_config_raises_invalid_config(
        self,
        connection_factory: Callable[..., ConnectionConfig],
        settings: dict[str, Any],
        message: str,
    ) -> None:
        client = AsyncMongoSideEffectExecutor()

        with pytest.raises(InvalidSideEffectProviderConfigError, match=message):
            await client.insert_one(
                connection=connection_factory(
                    name="main-mongo",
                    provider="mongo",
                    dsn=None,
                    settings=settings,
                ),
                collection="mock_events",
                document={"ok": True},
            )

    async def test_wraps_executor_creation_errors(self, mongo_connection: ConnectionConfig) -> None:
        FakePymongoAsyncMongoClient.create_client_error = RuntimeError("connect failed")
        client = AsyncMongoSideEffectExecutor()

        with pytest.raises(MongoSideEffectError) as exc_info:
            await client.insert_one(
                connection=mongo_connection,
                collection="mock_events",
                document={"ok": True},
            )

        assert exc_info.value.details == {"stage": "connect", "connection": "main-mongo"}

    async def test_wraps_insert_errors(self, mongo_connection: ConnectionConfig) -> None:
        FakePymongoAsyncMongoClient.command_error = RuntimeError("insert failed")
        client = AsyncMongoSideEffectExecutor()

        with pytest.raises(MongoSideEffectError) as exc_info:
            await client.insert_one(
                connection=mongo_connection,
                collection="mock_events",
                document={"ok": True},
            )

        assert exc_info.value.details == {
            "stage": "execute",
            "operation": "db_insert",
            "connection": "main-mongo",
            "collection": "mock_events",
        }

    async def test_wraps_update_errors(self, mongo_connection: ConnectionConfig) -> None:
        FakePymongoAsyncMongoClient.command_error = RuntimeError("update failed")
        client = AsyncMongoSideEffectExecutor()

        with pytest.raises(MongoSideEffectError) as exc_info:
            await client.update_one(
                connection=mongo_connection,
                collection="mock_state",
                filter_={"id": "state-1"},
                update={"$set": {"ok": True}},
            )

        assert exc_info.value.details == {
            "stage": "execute",
            "operation": "db_update",
            "connection": "main-mongo",
            "collection": "mock_state",
        }

    async def test_aclose_closes_all_executors_and_clears_cache(
        self,
        connection_factory: Callable[..., ConnectionConfig],
    ) -> None:
        client = AsyncMongoSideEffectExecutor()
        for connection in [
            connection_factory(
                name="first-mongo",
                provider="mongo",
                dsn=None,
                settings={"uri": "mongodb://localhost:27017", "database": "devmirror"},
            ),
            connection_factory(
                name="second-mongo",
                provider="mongo",
                dsn=None,
                settings={"uri": "mongodb://localhost:27018", "database": "devmirror"},
            ),
        ]:
            await client.insert_one(
                connection=connection,
                collection="mock_events",
                document={"ok": True},
            )

        await client.aclose()

        assert [client.closed for client in FakePymongoAsyncMongoClient.created_clients] == [
            True,
            True,
        ]
        assert client._clients == {}

    async def test_aclose_raises_mongo_error_when_executor_close_fails(
        self,
        connection_factory: Callable[..., ConnectionConfig],
    ) -> None:
        client = AsyncMongoSideEffectExecutor()
        for connection in [
            connection_factory(
                name="first-mongo",
                provider="mongo",
                dsn=None,
                settings={"uri": "mongodb://localhost:27017", "database": "devmirror"},
            ),
            connection_factory(
                name="second-mongo",
                provider="mongo",
                dsn=None,
                settings={"uri": "mongodb://localhost:27018", "database": "devmirror"},
            ),
        ]:
            await client.insert_one(
                connection=connection,
                collection="mock_events",
                document={"ok": True},
            )
        FakePymongoAsyncMongoClient.close_error_hosts = {"mongodb://localhost:27018"}

        with pytest.raises(MongoSideEffectError) as exc_info:
            await client.aclose()

        assert [client.closed for client in FakePymongoAsyncMongoClient.created_clients] == [
            True,
            True,
        ]
        assert client._clients == {}
        assert exc_info.value.details["stage"] == "close"
        assert exc_info.value.details["errors"] == ["close failed: mongodb://localhost:27018"]
