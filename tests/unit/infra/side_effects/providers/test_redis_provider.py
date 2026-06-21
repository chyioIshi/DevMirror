from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from app.domain.mocks.models import SideEffect, SideEffectContext, SideEffectType
from app.infra.exceptions import (
    ConnectionNotFoundError,
    InvalidSideEffectProviderConfigError,
    RedisSideEffectError,
)
from app.infra.side_effects import ConnectionConfig, ConnectionRegistry
from app.infra.side_effects.providers import RedisSideEffectProvider


@dataclass(slots=True)
class RedisCall:
    operation: str
    connection: ConnectionConfig
    parameters: dict[str, Any]


@dataclass(slots=True)
class FakeRedisClient:
    calls: list[RedisCall] = field(default_factory=list)
    error: RedisSideEffectError | None = None

    async def set_value(
        self,
        *,
        connection: ConnectionConfig,
        key: str,
        value: Any,
        ttl_seconds: int | None = None,
    ) -> None:
        if self.error is not None:
            raise self.error
        self.calls.append(
            RedisCall(
                operation="redis_set",
                connection=connection,
                parameters={"key": key, "value": value, "ttl_seconds": ttl_seconds},
            )
        )

    async def delete_key(
        self,
        *,
        connection: ConnectionConfig,
        key: str,
    ) -> int:
        if self.error is not None:
            raise self.error
        self.calls.append(
            RedisCall(
                operation="redis_delete",
                connection=connection,
                parameters={"key": key},
            )
        )
        return 1

    async def publish(
        self,
        *,
        connection: ConnectionConfig,
        channel: str,
        message: Any,
    ) -> int:
        if self.error is not None:
            raise self.error
        self.calls.append(
            RedisCall(
                operation="redis_publish",
                connection=connection,
                parameters={"channel": channel, "message": message},
            )
        )
        return 2


class TestRedisSideEffectProvider:
    async def test_sets_key_with_ttl(
        self,
        redis_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        redis_client = FakeRedisClient()
        effect = side_effect_factory(
            type=SideEffectType.REDIS_SET,
            provider="redis",
            target={"connection": "main-redis", "key": "cache:item"},
            payload_template={"id": "item-1"},
            options={"ttl_seconds": 30},
        )
        provider = RedisSideEffectProvider(
            connection_registry=redis_connection_registry,
            redis_client=redis_client,
        )

        result = await provider.execute(effect, side_effect_context)

        assert result.success is True
        assert result.details == {
            "connection": "main-redis",
            "operation": "redis_set",
            "key": "cache:item",
            "ttl_seconds": 30,
        }
        assert redis_client.calls == [
            RedisCall(
                operation="redis_set",
                connection=redis_connection_registry.get("main-redis"),
                parameters={
                    "key": "cache:item",
                    "value": {"id": "item-1"},
                    "ttl_seconds": 30,
                },
            )
        ]

    async def test_deletes_key(
        self,
        redis_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        effect = side_effect_factory(
            type=SideEffectType.REDIS_DELETE,
            provider="redis",
            target={"connection": "main-redis", "key": "cache:item"},
        )
        provider = RedisSideEffectProvider(
            connection_registry=redis_connection_registry,
            redis_client=FakeRedisClient(),
        )

        result = await provider.execute(effect, side_effect_context)

        assert result.success is True
        assert result.details["operation"] == "redis_delete"
        assert result.details["deleted_count"] == 1

    async def test_publishes_message(
        self,
        redis_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        effect = side_effect_factory(
            type=SideEffectType.REDIS_PUBLISH,
            provider="redis",
            target={"connection": "main-redis", "channel": "events"},
            payload_template={"id": "item-1"},
        )
        provider = RedisSideEffectProvider(
            connection_registry=redis_connection_registry,
            redis_client=FakeRedisClient(),
        )

        result = await provider.execute(effect, side_effect_context)

        assert result.success is True
        assert result.details["operation"] == "redis_publish"
        assert result.details["receiver_count"] == 2

    async def test_unknown_connection_fails_clearly(
        self,
        redis_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        effect = side_effect_factory(
            type=SideEffectType.REDIS_SET,
            provider="redis",
            target={"connection": "missing", "key": "cache:item"},
        )
        provider = RedisSideEffectProvider(
            connection_registry=redis_connection_registry,
            redis_client=FakeRedisClient(),
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
                    name="main-kafka",
                    provider="kafka",
                    settings={"bootstrap_servers": "localhost:9092"},
                )
            ]
        )
        effect = side_effect_factory(
            type=SideEffectType.REDIS_SET,
            provider="redis",
            target={"connection": "main-kafka", "key": "cache:item"},
        )
        provider = RedisSideEffectProvider(
            connection_registry=registry,
            redis_client=FakeRedisClient(),
        )

        with pytest.raises(
            InvalidSideEffectProviderConfigError,
            match="must reference a redis connection",
        ):
            await provider.execute(effect, side_effect_context)

    async def test_provider_mismatch_fails_clearly(
        self,
        redis_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
    ) -> None:
        effect = SideEffect(
            type=SideEffectType.REDIS_SET,
            provider="kafka",
            target={"connection": "main-redis", "key": "cache:item"},
            payload_template={"ok": True},
        )
        provider = RedisSideEffectProvider(
            connection_registry=redis_connection_registry,
            redis_client=FakeRedisClient(),
        )

        with pytest.raises(
            InvalidSideEffectProviderConfigError,
            match="provider must match redis",
        ):
            await provider.execute(effect, side_effect_context)

    async def test_unsupported_type_fails_clearly(
        self,
        redis_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
    ) -> None:
        effect = SideEffect(
            type=SideEffectType.HTTP_CALLBACK,
            provider="redis",
            target={"connection": "main-redis"},
            payload_template={"ok": True},
        )
        provider = RedisSideEffectProvider(
            connection_registry=redis_connection_registry,
            redis_client=FakeRedisClient(),
        )

        with pytest.raises(
            InvalidSideEffectProviderConfigError,
            match="supports only Redis side effect types",
        ):
            await provider.execute(effect, side_effect_context)

    async def test_rejects_missing_target_connection(
        self,
        redis_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
    ) -> None:
        effect = SideEffect(
            type=SideEffectType.REDIS_SET,
            provider="redis",
            target={"key": "cache:item"},
            payload_template={"ok": True},
        )
        provider = RedisSideEffectProvider(
            connection_registry=redis_connection_registry,
            redis_client=FakeRedisClient(),
        )

        with pytest.raises(
            InvalidSideEffectProviderConfigError,
            match="target.connection must be configured",
        ):
            await provider.execute(effect, side_effect_context)

    async def test_rejects_missing_key_for_set(
        self,
        redis_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
    ) -> None:
        effect = SideEffect(
            type=SideEffectType.REDIS_SET,
            provider="redis",
            target={"connection": "main-redis"},
            payload_template={"ok": True},
        )
        provider = RedisSideEffectProvider(
            connection_registry=redis_connection_registry,
            redis_client=FakeRedisClient(),
        )

        with pytest.raises(
            InvalidSideEffectProviderConfigError, match="target.key must be configured"
        ):
            await provider.execute(effect, side_effect_context)

    async def test_rejects_missing_channel_for_publish(
        self,
        redis_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
    ) -> None:
        effect = SideEffect(
            type=SideEffectType.REDIS_PUBLISH,
            provider="redis",
            target={"connection": "main-redis"},
            payload_template={"ok": True},
        )
        provider = RedisSideEffectProvider(
            connection_registry=redis_connection_registry,
            redis_client=FakeRedisClient(),
        )

        with pytest.raises(
            InvalidSideEffectProviderConfigError,
            match="target.channel must be configured",
        ):
            await provider.execute(effect, side_effect_context)

    async def test_rejects_invalid_ttl(
        self,
        redis_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        effect = side_effect_factory(
            type=SideEffectType.REDIS_SET,
            provider="redis",
            target={"connection": "main-redis", "key": "cache:item"},
            options={"ttl_seconds": 0},
        )
        provider = RedisSideEffectProvider(
            connection_registry=redis_connection_registry,
            redis_client=FakeRedisClient(),
        )

        with pytest.raises(
            InvalidSideEffectProviderConfigError,
            match="options.ttl_seconds must be a positive integer",
        ):
            await provider.execute(effect, side_effect_context)

    async def test_redis_error_returns_failed_execution_result(
        self,
        redis_connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        effect = side_effect_factory(
            type=SideEffectType.REDIS_SET,
            provider="redis",
            target={"connection": "main-redis", "key": "cache:item"},
        )
        provider = RedisSideEffectProvider(
            connection_registry=redis_connection_registry,
            redis_client=FakeRedisClient(error=RedisSideEffectError("redis failed")),
        )

        result = await provider.execute(effect, side_effect_context)

        assert result.success is False
        assert result.details == {"connection": "main-redis", "operation": "redis_set"}
        assert result.error == "redis failed"


class TestRedisSideEffectProviderArchitecture:
    def test_domain_and_application_do_not_import_redis_client(self) -> None:
        forbidden_roots = [Path("app/domain"), Path("app/application")]

        matches = [
            path
            for root in forbidden_roots
            for path in root.rglob("*.py")
            if any(
                line.startswith(("import redis", "from redis"))
                for line in path.read_text(encoding="utf-8").splitlines()
            )
        ]

        assert matches == []
