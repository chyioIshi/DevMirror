"""redis.asyncio-backed Redis side effect executor."""

import asyncio
import json
from dataclasses import dataclass
from typing import Any

import redis.asyncio as redis

from app.helpers.side_effect_provider_validation import SideEffectProviderValidation
from app.infra.exceptions import InvalidSideEffectProviderConfigError, RedisSideEffectError
from app.infra.side_effects.connection_config import ConnectionConfig

RedisCommandValue = bytes | str


@dataclass(slots=True, frozen=True)
class RedisSideEffectExecutorConfig:
    """Validated Redis executor configuration."""

    connection_name: str
    url: str
    socket_timeout: float | None
    socket_connect_timeout: float | None
    max_connections: int | None

    def key(self) -> tuple[str, str, float | None, float | None, int | None]:
        """Returns the cache key for a Redis executor created from this config."""
        return (
            self.connection_name,
            self.url,
            self.socket_timeout,
            self.socket_connect_timeout,
            self.max_connections,
        )

    def create_client_map(self) -> dict[str, Any]:
        """Returns redis.Redis.from_url params in dict."""
        params: dict[str, Any] = {"url": self.url}
        if self.socket_timeout is not None:
            params["socket_timeout"] = self.socket_timeout
        if self.socket_connect_timeout is not None:
            params["socket_connect_timeout"] = self.socket_connect_timeout
        if self.max_connections is not None:
            params["max_connections"] = self.max_connections
        return params


class AsyncRedisSideEffectExecutor:
    """Executes Redis side effect commands using reusable async Redis clients."""

    def __init__(self) -> None:
        """Initializes an empty Redis executor cache."""
        self._clients: dict[
            tuple[str, str, float | None, float | None, int | None],
            redis.Redis,
        ] = {}
        self._client_lock = asyncio.Lock()

    async def set_value(
        self,
        *,
        connection: ConnectionConfig,
        key: str,
        value: Any,
        ttl_seconds: int | None = None,
    ) -> None:
        """Sets one Redis key to the serialized rendered value."""
        client = await self._client(connection)
        serialized = self._serialize_value(
            value,
            operation="redis_set",
            connection=connection.name,
        )
        try:
            await client.set(name=key, value=serialized, ex=ttl_seconds)
        except Exception as exc:
            raise RedisSideEffectError(
                "Redis SET command failed",
                details={
                    "stage": "execute",
                    "operation": "redis_set",
                    "connection": connection.name,
                },
            ) from exc

    async def delete_key(
        self,
        *,
        connection: ConnectionConfig,
        key: str,
    ) -> int:
        """Deletes one Redis key and returns deleted key count."""
        client = await self._client(connection)
        try:
            deleted_count = await client.delete(key)
        except Exception as exc:
            raise RedisSideEffectError(
                "Redis DEL command failed",
                details={
                    "stage": "execute",
                    "operation": "redis_delete",
                    "connection": connection.name,
                },
            ) from exc
        return int(deleted_count)

    async def publish(
        self,
        *,
        connection: ConnectionConfig,
        channel: str,
        message: Any,
    ) -> int:
        """Publishes the serialized rendered message to a Redis channel."""
        client = await self._client(connection)
        serialized = self._serialize_value(
            message,
            operation="redis_publish",
            connection=connection.name,
        )
        try:
            receiver_count = await client.publish(channel, serialized)
        except Exception as exc:
            raise RedisSideEffectError(
                "Redis PUBLISH command failed",
                details={
                    "stage": "execute",
                    "operation": "redis_publish",
                    "connection": connection.name,
                },
            ) from exc
        return int(receiver_count)

    async def aclose(self) -> None:
        """Closes cached Redis clients."""
        async with self._client_lock:
            try:
                results: list[object] = await asyncio.gather(
                    *(client.aclose() for client in self._clients.values()),
                    return_exceptions=True,
                )
            finally:
                self._clients.clear()

        errors = [str(result) for result in results if isinstance(result, Exception)]
        if errors:
            raise RedisSideEffectError(
                "Redis client close failed",
                details={"stage": "close", "errors": errors},
            )

    async def _client(self, connection: ConnectionConfig) -> redis.Redis:
        config = self._client_config(connection)
        key = config.key()
        client = self._clients.get(key)
        if client is not None:
            return client

        async with self._client_lock:
            client = self._clients.get(key)
            if client is not None:
                return client

            try:
                client = redis.Redis.from_url(**config.create_client_map())
            except Exception as exc:
                raise RedisSideEffectError(
                    "Redis client creation failed",
                    details={"stage": "connect", "connection": connection.name},
                ) from exc

            self._clients[key] = client
            return client

    def _client_config(self, connection: ConnectionConfig) -> RedisSideEffectExecutorConfig:
        return RedisSideEffectExecutorConfig(
            connection_name=connection.name,
            url=self._url(connection),
            socket_timeout=SideEffectProviderValidation.optional_positive_number(
                connection.settings,
                "socket_timeout",
                "connection.settings.socket_timeout",
                subject="Redis",
            ),
            socket_connect_timeout=SideEffectProviderValidation.optional_positive_number(
                connection.settings,
                "socket_connect_timeout",
                "connection.settings.socket_connect_timeout",
                subject="Redis",
            ),
            max_connections=SideEffectProviderValidation.optional_positive_int(
                connection.settings,
                "max_connections",
                "connection.settings.max_connections",
                subject="Redis",
            ),
        )

    def _url(self, connection: ConnectionConfig) -> str:
        url = connection.settings.get("url")
        if isinstance(url, str) and url.strip():
            return url
        raise InvalidSideEffectProviderConfigError(
            "Redis connection.settings.url must be configured",
            details={"field": "connection.settings.url"},
        )

    def _serialize_value(
        self,
        value: Any,
        *,
        operation: str,
        connection: str,
    ) -> RedisCommandValue:
        if isinstance(value, bytes | str):
            return value
        try:
            return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        except (TypeError, ValueError) as exc:
            raise RedisSideEffectError(
                "Redis value serialization failed",
                details={
                    "stage": "serialization",
                    "operation": operation,
                    "connection": connection,
                },
            ) from exc
