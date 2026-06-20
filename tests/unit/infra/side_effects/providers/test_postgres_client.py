import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, ClassVar

import pytest

from app.infra.exceptions import InvalidSideEffectProviderConfigError, PostgresInsertError
from app.infra.side_effects import ConnectionConfig
from app.infra.side_effects.providers import AsyncPostgresClient


@dataclass(slots=True)
class ExecutedStatement:
    statement: str
    parameters: list[Any]


@dataclass(slots=True)
class FakeAsyncpgPool:
    created_pools: ClassVar[list["FakeAsyncpgPool"]] = []
    create_pool_error: ClassVar[Exception | None] = None
    execute_error: ClassVar[Exception | None] = None
    close_error_dsns: ClassVar[set[str]] = set()

    kwargs: dict[str, Any]
    closed: bool = False
    executed_statements: list[ExecutedStatement] = field(default_factory=list)

    def __post_init__(self) -> None:
        type(self).created_pools.append(self)

    async def execute(self, statement: str, *parameters: Any) -> str:
        if type(self).execute_error is not None:
            raise type(self).execute_error
        self.executed_statements.append(
            ExecutedStatement(
                statement=statement,
                parameters=list(parameters),
            )
        )
        return "INSERT 0 1"

    async def close(self) -> None:
        self.closed = True
        if self.kwargs["dsn"] in type(self).close_error_dsns:
            raise RuntimeError(f"close failed: {self.kwargs['dsn']}")


class TestAsyncPostgresClient:
    @pytest.fixture(autouse=True)
    def reset_fake_asyncpg_pool(self, monkeypatch: pytest.MonkeyPatch) -> None:
        FakeAsyncpgPool.created_pools.clear()
        FakeAsyncpgPool.create_pool_error = None
        FakeAsyncpgPool.execute_error = None
        FakeAsyncpgPool.close_error_dsns = set()

        async def create_pool(**kwargs: Any) -> FakeAsyncpgPool:
            await asyncio.sleep(0)
            if FakeAsyncpgPool.create_pool_error is not None:
                raise FakeAsyncpgPool.create_pool_error
            return FakeAsyncpgPool(kwargs=kwargs)

        monkeypatch.setattr(
            "app.infra.side_effects.providers.postgres_client.asyncpg.create_pool",
            create_pool,
        )

    async def test_executes_parameterized_insert(
        self,
        connection_factory: Callable[..., ConnectionConfig],
    ) -> None:
        executor = AsyncPostgresClient()
        connection = connection_factory()

        result = await executor.execute_insert(
            connection=connection,
            statement='INSERT INTO "events" ("name") VALUES ($1)',
            parameters=["created"],
        )

        assert result == {"command_tag": "INSERT 0 1"}
        assert FakeAsyncpgPool.created_pools[0].executed_statements == [
            ExecutedStatement(
                statement='INSERT INTO "events" ("name") VALUES ($1)',
                parameters=["created"],
            )
        ]

    async def test_missing_dsn_raises_invalid_config(self) -> None:
        executor = AsyncPostgresClient()

        with pytest.raises(
            InvalidSideEffectProviderConfigError,
            match="connection.settings.dsn must be configured",
        ):
            await executor.execute_insert(
                connection=ConnectionConfig(
                    name="main-postgres",
                    provider="postgres",
                    settings={},
                ),
                statement='INSERT INTO "events" ("name") VALUES ($1)',
                parameters=["created"],
            )

    async def test_invalid_min_size_raises_invalid_config(
        self,
        connection_factory: Callable[..., ConnectionConfig],
    ) -> None:
        executor = AsyncPostgresClient()

        with pytest.raises(
            InvalidSideEffectProviderConfigError,
            match="connection.settings.min_size must be a positive integer",
        ):
            await executor.execute_insert(
                connection=connection_factory(settings={"min_size": 0}),
                statement='INSERT INTO "events" ("name") VALUES ($1)',
                parameters=["created"],
            )

    async def test_invalid_max_size_raises_invalid_config(
        self,
        connection_factory: Callable[..., ConnectionConfig],
    ) -> None:
        executor = AsyncPostgresClient()

        with pytest.raises(
            InvalidSideEffectProviderConfigError,
            match="connection.settings.max_size must be a positive integer",
        ):
            await executor.execute_insert(
                connection=connection_factory(settings={"max_size": True}),
                statement='INSERT INTO "events" ("name") VALUES ($1)',
                parameters=["created"],
            )

    async def test_max_size_less_than_min_size_raises_invalid_config(
        self,
        connection_factory: Callable[..., ConnectionConfig],
    ) -> None:
        executor = AsyncPostgresClient()

        with pytest.raises(
            InvalidSideEffectProviderConfigError,
            match="max_size must be greater than or equal to min_size",
        ):
            await executor.execute_insert(
                connection=connection_factory(settings={"min_size": 5, "max_size": 2}),
                statement='INSERT INTO "events" ("name") VALUES ($1)',
                parameters=["created"],
            )

    async def test_invalid_command_timeout_raises_invalid_config(
        self,
        connection_factory: Callable[..., ConnectionConfig],
    ) -> None:
        executor = AsyncPostgresClient()

        with pytest.raises(
            InvalidSideEffectProviderConfigError,
            match="connection.settings.command_timeout must be a positive number",
        ):
            await executor.execute_insert(
                connection=connection_factory(settings={"command_timeout": False}),
                statement='INSERT INTO "events" ("name") VALUES ($1)',
                parameters=["created"],
            )

    async def test_passes_pool_options_to_asyncpg_create_pool(
        self,
        connection_factory: Callable[..., ConnectionConfig],
    ) -> None:
        executor = AsyncPostgresClient()

        await executor.execute_insert(
            connection=connection_factory(
                settings={"min_size": 1, "max_size": 4, "command_timeout": 2.5},
            ),
            statement='INSERT INTO "events" ("name") VALUES ($1)',
            parameters=["created"],
        )

        assert FakeAsyncpgPool.created_pools[0].kwargs == {
            "dsn": "postgresql://localhost:5432/devmirror",
            "min_size": 1,
            "max_size": 4,
            "command_timeout": 2.5,
        }

    async def test_creates_pool_once_for_concurrent_calls_with_same_settings(
        self,
        connection_factory: Callable[..., ConnectionConfig],
    ) -> None:
        executor = AsyncPostgresClient()
        connection = connection_factory()

        await asyncio.gather(
            *[
                executor.execute_insert(
                    connection=connection,
                    statement='INSERT INTO "events" ("name") VALUES ($1)',
                    parameters=[f"created-{index}"],
                )
                for index in range(5)
            ]
        )

        assert len(FakeAsyncpgPool.created_pools) == 1
        assert len(FakeAsyncpgPool.created_pools[0].executed_statements) == 5

    async def test_reuses_cached_pool(
        self,
        connection_factory: Callable[..., ConnectionConfig],
    ) -> None:
        executor = AsyncPostgresClient()
        connection = connection_factory()

        await executor.execute_insert(
            connection=connection,
            statement='INSERT INTO "events" ("name") VALUES ($1)',
            parameters=["first"],
        )
        await executor.execute_insert(
            connection=connection,
            statement='INSERT INTO "events" ("name") VALUES ($1)',
            parameters=["second"],
        )

        assert len(FakeAsyncpgPool.created_pools) == 1
        assert len(FakeAsyncpgPool.created_pools[0].executed_statements) == 2

    async def test_creates_different_pools_for_different_names_dsn_or_options(
        self,
        connection_factory: Callable[..., ConnectionConfig],
    ) -> None:
        executor = AsyncPostgresClient()

        for connection in [
            connection_factory(name="first-postgres"),
            connection_factory(name="second-postgres"),
            connection_factory(name="first-postgres", dsn="postgresql://localhost:5432/other"),
            connection_factory(name="first-postgres", settings={"min_size": 2}),
        ]:
            await executor.execute_insert(
                connection=connection,
                statement='INSERT INTO "events" ("name") VALUES ($1)',
                parameters=["created"],
            )

        assert len(FakeAsyncpgPool.created_pools) == 4

    async def test_wraps_create_pool_errors(
        self,
        connection_factory: Callable[..., ConnectionConfig],
    ) -> None:
        FakeAsyncpgPool.create_pool_error = RuntimeError("connect failed")
        executor = AsyncPostgresClient()

        with pytest.raises(PostgresInsertError) as exc_info:
            await executor.execute_insert(
                connection=connection_factory(),
                statement='INSERT INTO "events" ("name") VALUES ($1)',
                parameters=["created"],
            )

        assert exc_info.value.details == {
            "stage": "connect",
            "connection": "main-postgres",
        }

    async def test_wraps_execute_errors(
        self,
        connection_factory: Callable[..., ConnectionConfig],
    ) -> None:
        FakeAsyncpgPool.execute_error = RuntimeError("database failed")
        executor = AsyncPostgresClient()

        with pytest.raises(PostgresInsertError) as exc_info:
            await executor.execute_insert(
                connection=connection_factory(),
                statement='INSERT INTO "events" ("name") VALUES ($1)',
                parameters=["created"],
            )

        assert exc_info.value.details == {
            "stage": "execute",
            "connection": "main-postgres",
        }

    async def test_aclose_closes_all_pools_and_clears_cache(
        self,
        connection_factory: Callable[..., ConnectionConfig],
    ) -> None:
        executor = AsyncPostgresClient()
        for connection in [
            connection_factory(name="first-postgres"),
            connection_factory(name="second-postgres"),
        ]:
            await executor.execute_insert(
                connection=connection,
                statement='INSERT INTO "events" ("name") VALUES ($1)',
                parameters=["created"],
            )

        await executor.aclose()

        assert [pool.closed for pool in FakeAsyncpgPool.created_pools] == [True, True]
        assert executor._pools == {}

    async def test_aclose_raises_postgres_insert_error_when_pool_close_fails(
        self,
        connection_factory: Callable[..., ConnectionConfig],
    ) -> None:
        executor = AsyncPostgresClient()
        for connection in [
            connection_factory(name="first-postgres"),
            connection_factory(
                name="second-postgres",
                dsn="postgresql://localhost:5432/other",
            ),
        ]:
            await executor.execute_insert(
                connection=connection,
                statement='INSERT INTO "events" ("name") VALUES ($1)',
                parameters=["created"],
            )
        FakeAsyncpgPool.close_error_dsns = {"postgresql://localhost:5432/other"}

        with pytest.raises(PostgresInsertError) as exc_info:
            await executor.aclose()

        assert [pool.closed for pool in FakeAsyncpgPool.created_pools] == [True, True]
        assert executor._pools == {}
        assert exc_info.value.details["stage"] == "close"
        assert exc_info.value.details["errors"] == [
            "close failed: postgresql://localhost:5432/other"
        ]
