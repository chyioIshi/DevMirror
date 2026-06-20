"""asyncpg-backed Postgres insert executor."""

import asyncio
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import asyncpg

from app.infra.exceptions import InvalidSideEffectProviderConfigError, PostgresInsertError
from app.infra.side_effects.connection_config import ConnectionConfig


@dataclass(slots=True, frozen=True)
class PostgresPoolConfig:
    """Validated Postgres pool configuration."""

    connection_name: str
    dsn: str
    min_size: int | None
    max_size: int | None
    command_timeout: float | None

    def key(self) -> tuple[str, str, int | None, int | None, float | None]:
        """Returns the cache key for a pool created from this config."""
        return (
            self.connection_name,
            self.dsn,
            self.min_size,
            self.max_size,
            self.command_timeout,
        )

    def create_pool_map(self) -> dict[str, Any]:
        """Returns asyncpg.create_pool params in dict."""
        kwargs: dict[str, Any] = {"dsn": self.dsn}
        if self.min_size is not None:
            kwargs["min_size"] = self.min_size
        if self.max_size is not None:
            kwargs["max_size"] = self.max_size
        if self.command_timeout is not None:
            kwargs["command_timeout"] = self.command_timeout
        return kwargs


class AsyncPostgresClient:
    """Executes parameterized Postgres INSERT statements using reusable pools."""

    def __init__(self) -> None:
        """Initializes an empty connection pool cache."""
        self._pools: dict[
            tuple[str, str, int | None, int | None, float | None],
            asyncpg.Pool,
        ] = {}
        self._pool_lock = asyncio.Lock()

    async def execute_insert(
        self,
        *,
        connection: ConnectionConfig,
        statement: str,
        parameters: Sequence[Any],
    ) -> dict[str, Any]:
        """Executes one parameterized INSERT statement."""
        pool = await self._pool(connection)
        try:
            command_tag = await pool.execute(statement, *parameters)
        except Exception as exc:
            raise PostgresInsertError(
                "Postgres insert execution failed",
                details={"stage": "execute", "connection": connection.name},
            ) from exc

        return {"command_tag": command_tag}

    async def aclose(self) -> None:
        """Closes cached Postgres pools."""
        async with self._pool_lock:
            try:
                results: list[object] = await asyncio.gather(
                    *(pool.close() for pool in self._pools.values()),
                    return_exceptions=True,
                )
            finally:
                self._pools.clear()

        errors = [str(result) for result in results if isinstance(result, Exception)]
        if errors:
            raise PostgresInsertError(
                "Postgres pool close failed",
                details={"stage": "close", "errors": errors},
            )

    async def _pool(self, connection: ConnectionConfig) -> asyncpg.Pool:
        config = self._pool_config(connection)
        key = config.key()
        pool = self._pools.get(key)
        if pool is not None:
            return pool

        async with self._pool_lock:
            pool = self._pools.get(key)
            if pool is not None:
                return pool

            try:
                pool = await asyncpg.create_pool(**config.create_pool_map())
            except Exception as exc:
                raise PostgresInsertError(
                    "Postgres pool creation failed",
                    details={"stage": "connect", "connection": connection.name},
                ) from exc

            self._pools[key] = pool
            return pool

    def _pool_config(self, connection: ConnectionConfig) -> PostgresPoolConfig:
        min_size = self._optional_positive_int(connection.settings, "min_size")
        max_size = self._optional_positive_int(connection.settings, "max_size")
        if min_size is not None and max_size is not None and max_size < min_size:
            raise InvalidSideEffectProviderConfigError(
                "Postgres connection.settings.max_size must be greater than or equal to min_size",
                details={"field": "connection.settings.max_size"},
            )

        return PostgresPoolConfig(
            connection_name=connection.name,
            dsn=self._dsn(connection),
            min_size=min_size,
            max_size=max_size,
            command_timeout=self._optional_positive_number(
                connection.settings,
                "command_timeout",
            ),
        )

    def _dsn(self, connection: ConnectionConfig) -> str:
        dsn = connection.settings.get("dsn")
        if isinstance(dsn, str) and dsn.strip():
            return dsn
        raise InvalidSideEffectProviderConfigError(
            "Postgres connection.settings.dsn must be configured",
            details={"field": "connection.settings.dsn"},
        )

    def _optional_positive_int(
        self,
        settings: dict[str, Any],
        key: str,
    ) -> int | None:
        value = settings.get(key)
        if value is None:
            return None
        if isinstance(value, int) and not isinstance(value, bool) and value > 0:
            return value
        raise InvalidSideEffectProviderConfigError(
            f"Postgres connection.settings.{key} must be a positive integer",
            details={"field": f"connection.settings.{key}"},
        )

    def _optional_positive_number(
        self,
        settings: dict[str, Any],
        key: str,
    ) -> float | None:
        value = settings.get(key)
        if value is None:
            return None
        if isinstance(value, int | float) and not isinstance(value, bool) and value > 0:
            return float(value)
        raise InvalidSideEffectProviderConfigError(
            f"Postgres connection.settings.{key} must be a positive number",
            details={"field": f"connection.settings.{key}"},
        )
