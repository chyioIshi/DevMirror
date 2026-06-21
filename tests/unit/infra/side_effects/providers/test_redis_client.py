import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar

import pytest

from app.infra.exceptions import InvalidSideEffectProviderConfigError, RedisSideEffectError
from app.infra.side_effects import ConnectionConfig
from app.infra.side_effects.providers import AsyncRedisClient


@dataclass(slots=True)
class RedisCommand:
    name: str
    parameters: dict[str, Any]


@dataclass(slots=True)
class FakeRedis:
    created_clients: ClassVar[list["FakeRedis"]] = []
    create_client_error: ClassVar[Exception | None] = None
    command_error: ClassVar[Exception | None] = None
    close_error_urls: ClassVar[set[str]] = set()

    params: dict[str, Any]
    closed: bool = False
    commands: list[RedisCommand] = field(default_factory=list)

    def __post_init__(self) -> None:
        type(self).created_clients.append(self)

    async def set(self, *, name: str, value: Any, ex: int | None = None) -> None:
        if type(self).command_error is not None:
            raise type(self).command_error
        self.commands.append(
            RedisCommand(
                name="set",
                parameters={"name": name, "value": value, "ex": ex},
            )
        )

    async def delete(self, key: str) -> int:
        if type(self).command_error is not None:
            raise type(self).command_error
        self.commands.append(RedisCommand(name="delete", parameters={"key": key}))
        return 1

    async def publish(self, channel: str, message: Any) -> int:
        if type(self).command_error is not None:
            raise type(self).command_error
        self.commands.append(
            RedisCommand(
                name="publish",
                parameters={"channel": channel, "message": message},
            )
        )
        return 2

    async def aclose(self) -> None:
        self.closed = True
        if self.params["url"] in type(self).close_error_urls:
            raise RuntimeError(f"close failed: {self.params['url']}")


class TestAsyncRedisClient:
    @pytest.fixture(autouse=True)
    def reset_fake_redis(self, monkeypatch: pytest.MonkeyPatch) -> None:
        FakeRedis.created_clients.clear()
        FakeRedis.create_client_error = None
        FakeRedis.command_error = None
        FakeRedis.close_error_urls = set()

        def from_url(**kwargs: Any) -> FakeRedis:
            if FakeRedis.create_client_error is not None:
                raise FakeRedis.create_client_error
            return FakeRedis(params=kwargs)

        monkeypatch.setattr(
            "app.infra.side_effects.providers.redis_client.redis.Redis.from_url",
            from_url,
        )

    @pytest.fixture
    def redis_connection(
        self,
        connection_factory: Callable[..., ConnectionConfig],
    ) -> ConnectionConfig:
        return connection_factory(
            name="main-redis",
            provider="redis",
            dsn=None,
            settings={"url": "redis://localhost:6379/0"},
        )

    async def test_creates_client_once_for_same_connection_settings(
        self,
        redis_connection: ConnectionConfig,
    ) -> None:
        client = AsyncRedisClient()

        await asyncio.gather(
            *[
                client.set_value(
                    connection=redis_connection,
                    key=f"cache:item:{index}",
                    value={"index": index},
                )
                for index in range(5)
            ]
        )

        assert len(FakeRedis.created_clients) == 1
        assert len(FakeRedis.created_clients[0].commands) == 5

    async def test_reuses_cached_client(self, redis_connection: ConnectionConfig) -> None:
        client = AsyncRedisClient()

        await client.set_value(connection=redis_connection, key="first", value={"ok": True})
        await client.set_value(connection=redis_connection, key="second", value={"ok": False})

        assert len(FakeRedis.created_clients) == 1
        assert [
            command.parameters["name"] for command in FakeRedis.created_clients[0].commands
        ] == [
            "first",
            "second",
        ]

    async def test_creates_different_clients_for_different_options(
        self,
        connection_factory: Callable[..., ConnectionConfig],
    ) -> None:
        client = AsyncRedisClient()

        for connection in [
            connection_factory(
                name="first-redis",
                provider="redis",
                dsn=None,
                settings={"url": "redis://localhost:6379/0"},
            ),
            connection_factory(
                name="second-redis",
                provider="redis",
                dsn=None,
                settings={"url": "redis://localhost:6379/0"},
            ),
            connection_factory(
                name="first-redis",
                provider="redis",
                dsn=None,
                settings={"url": "redis://localhost:6380/0"},
            ),
            connection_factory(
                name="first-redis",
                provider="redis",
                dsn=None,
                settings={"url": "redis://localhost:6379/0", "max_connections": 2},
            ),
        ]:
            await client.set_value(connection=connection, key="cache:item", value={"ok": True})

        assert len(FakeRedis.created_clients) == 4

    async def test_passes_client_options_to_redis_from_url(
        self,
        connection_factory: Callable[..., ConnectionConfig],
    ) -> None:
        client = AsyncRedisClient()

        await client.set_value(
            connection=connection_factory(
                name="main-redis",
                provider="redis",
                dsn=None,
                settings={
                    "url": "redis://localhost:6379/0",
                    "socket_timeout": 2,
                    "socket_connect_timeout": 1.5,
                    "max_connections": 5,
                },
            ),
            key="cache:item",
            value={"ok": True},
        )

        assert FakeRedis.created_clients[0].params == {
            "url": "redis://localhost:6379/0",
            "socket_timeout": 2.0,
            "socket_connect_timeout": 1.5,
            "max_connections": 5,
        }

    async def test_set_serializes_dict_list_string_and_bytes(
        self,
        redis_connection: ConnectionConfig,
    ) -> None:
        client = AsyncRedisClient()

        await client.set_value(connection=redis_connection, key="dict", value={"id": "item-1"})
        await client.set_value(connection=redis_connection, key="list", value=[1, 2])
        await client.set_value(connection=redis_connection, key="string", value="raw")
        await client.set_value(connection=redis_connection, key="bytes", value=b"raw")

        assert [
            command.parameters["value"] for command in FakeRedis.created_clients[0].commands
        ] == [
            '{"id":"item-1"}',
            "[1,2]",
            "raw",
            b"raw",
        ]

    async def test_delete_key_returns_deleted_count(
        self, redis_connection: ConnectionConfig
    ) -> None:
        client = AsyncRedisClient()

        result = await client.delete_key(connection=redis_connection, key="cache:item")

        assert result == 1
        assert FakeRedis.created_clients[0].commands == [
            RedisCommand(name="delete", parameters={"key": "cache:item"})
        ]

    async def test_publish_serializes_message(self, redis_connection: ConnectionConfig) -> None:
        client = AsyncRedisClient()

        result = await client.publish(
            connection=redis_connection,
            channel="events",
            message={"id": "item-1"},
        )

        assert result == 2
        assert FakeRedis.created_clients[0].commands == [
            RedisCommand(
                name="publish",
                parameters={"channel": "events", "message": '{"id":"item-1"}'},
            )
        ]

    async def test_missing_url_raises_invalid_config(self) -> None:
        client = AsyncRedisClient()

        with pytest.raises(
            InvalidSideEffectProviderConfigError,
            match="connection.settings.url must be configured",
        ):
            await client.set_value(
                connection=ConnectionConfig(
                    name="main-redis",
                    provider="redis",
                    settings={},
                ),
                key="cache:item",
                value={"ok": True},
            )

    @pytest.mark.parametrize(
        ("settings", "message"),
        [
            (
                {"url": "redis://localhost:6379/0", "socket_timeout": False},
                "connection.settings.socket_timeout must be a positive number",
            ),
            (
                {"url": "redis://localhost:6379/0", "socket_connect_timeout": 0},
                "connection.settings.socket_connect_timeout must be a positive number",
            ),
            (
                {"url": "redis://localhost:6379/0", "max_connections": 0},
                "connection.settings.max_connections must be a positive integer",
            ),
        ],
    )
    async def test_invalid_client_options_raise_invalid_config(
        self,
        connection_factory: Callable[..., ConnectionConfig],
        settings: dict[str, Any],
        message: str,
    ) -> None:
        client = AsyncRedisClient()

        with pytest.raises(InvalidSideEffectProviderConfigError, match=message):
            await client.set_value(
                connection=connection_factory(
                    name="main-redis",
                    provider="redis",
                    dsn=None,
                    settings=settings,
                ),
                key="cache:item",
                value={"ok": True},
            )

    async def test_wraps_client_creation_errors(self, redis_connection: ConnectionConfig) -> None:
        FakeRedis.create_client_error = RuntimeError("connect failed")
        client = AsyncRedisClient()

        with pytest.raises(RedisSideEffectError) as exc_info:
            await client.set_value(
                connection=redis_connection, key="cache:item", value={"ok": True}
            )

        assert exc_info.value.details == {
            "stage": "connect",
            "connection": "main-redis",
        }

    async def test_wraps_command_errors(self, redis_connection: ConnectionConfig) -> None:
        FakeRedis.command_error = RuntimeError("command failed")
        client = AsyncRedisClient()

        with pytest.raises(RedisSideEffectError) as exc_info:
            await client.set_value(
                connection=redis_connection, key="cache:item", value={"ok": True}
            )

        assert exc_info.value.details == {
            "stage": "execute",
            "operation": "redis_set",
            "connection": "main-redis",
        }

    async def test_wraps_serialization_errors(self, redis_connection: ConnectionConfig) -> None:
        client = AsyncRedisClient()

        with pytest.raises(RedisSideEffectError) as exc_info:
            await client.set_value(connection=redis_connection, key="cache:item", value=object())

        assert exc_info.value.details == {
            "stage": "serialization",
            "operation": "redis_set",
            "connection": "main-redis",
        }

    async def test_aclose_closes_all_clients_and_clears_cache(
        self,
        connection_factory: Callable[..., ConnectionConfig],
    ) -> None:
        client = AsyncRedisClient()
        for connection in [
            connection_factory(
                name="first-redis",
                provider="redis",
                dsn=None,
                settings={"url": "redis://localhost:6379/0"},
            ),
            connection_factory(
                name="second-redis",
                provider="redis",
                dsn=None,
                settings={"url": "redis://localhost:6380/0"},
            ),
        ]:
            await client.set_value(connection=connection, key="cache:item", value={"ok": True})

        await client.aclose()

        assert [redis_client.closed for redis_client in FakeRedis.created_clients] == [True, True]
        assert client._clients == {}

    async def test_aclose_raises_redis_error_when_client_close_fails(
        self,
        connection_factory: Callable[..., ConnectionConfig],
    ) -> None:
        client = AsyncRedisClient()
        for connection in [
            connection_factory(
                name="first-redis",
                provider="redis",
                dsn=None,
                settings={"url": "redis://localhost:6379/0"},
            ),
            connection_factory(
                name="second-redis",
                provider="redis",
                dsn=None,
                settings={"url": "redis://localhost:6380/0"},
            ),
        ]:
            await client.set_value(connection=connection, key="cache:item", value={"ok": True})
        FakeRedis.close_error_urls = {"redis://localhost:6380/0"}

        with pytest.raises(RedisSideEffectError) as exc_info:
            await client.aclose()

        assert [redis_client.closed for redis_client in FakeRedis.created_clients] == [True, True]
        assert client._clients == {}
        assert exc_info.value.details["stage"] == "close"
        assert exc_info.value.details["errors"] == ["close failed: redis://localhost:6380/0"]


class TestAsyncRedisClientArchitecture:
    def test_redis_library_imports_only_in_redis_client(self) -> None:
        matches = [
            path
            for path in Path("app").rglob("*.py")
            if path != Path("app/infra/side_effects/providers/redis_client.py")
            if any(
                line.startswith(("import redis", "from redis"))
                for line in path.read_text(encoding="utf-8").splitlines()
            )
        ]

        assert matches == []
