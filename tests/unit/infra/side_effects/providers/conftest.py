from collections.abc import Callable
from typing import Any

import pytest

from app.domain.mocks.models import SideEffect, SideEffectContext, SideEffectType
from app.infra.side_effects import ConnectionConfig, ConnectionRegistry


@pytest.fixture
def side_effect_factory() -> Callable[..., SideEffect]:
    def create_side_effect(
        *,
        type: SideEffectType,
        provider: str,
        target: dict[str, Any],
        payload_template: dict[str, Any] | None = None,
        options: dict[str, Any] | None = None,
    ) -> SideEffect:
        return SideEffect(
            type=type,
            provider=provider,
            target=target,
            payload_template=payload_template if payload_template is not None else {"ok": True},
            options=options or {},
        )

    return create_side_effect


@pytest.fixture
def connection_factory() -> Callable[..., ConnectionConfig]:
    def create_connection(
        *,
        name: str = "main-postgres",
        provider: str = "postgres",
        dsn: str | None = "postgresql://localhost:5432/devmirror",
        settings: dict[str, Any] | None = None,
    ) -> ConnectionConfig:
        connection_settings = dict(settings or {})
        if dsn is not None:
            connection_settings["dsn"] = dsn
        return ConnectionConfig(
            name=name,
            provider=provider,
            settings=connection_settings,
        )

    return create_connection


@pytest.fixture
def side_effect_context() -> SideEffectContext:
    return SideEffectContext(
        request={},
        mock={"id": "mock-1"},
        response={"status_code": 200},
        execution={"request_id": "request-1"},
    )


@pytest.fixture
def connection_registry() -> ConnectionRegistry:
    return ConnectionRegistry(
        connections=[
            ConnectionConfig(
                name="main-http",
                provider="http",
                settings={
                    "base_url": "https://callback.test/api",
                    "timeout_seconds": 5,
                    "default_headers": {
                        "X-Default": "default",
                        "X-Override": "default",
                    },
                },
            ),
        ],
    )


@pytest.fixture
def kafka_connection_registry() -> ConnectionRegistry:
    return ConnectionRegistry(
        connections=[
            ConnectionConfig(
                name="main-kafka",
                provider="kafka",
                settings={
                    "bootstrap_servers": "localhost:9092",
                    "client_id": "devmirror-tests",
                },
            ),
        ],
    )


@pytest.fixture
def postgres_connection_registry() -> ConnectionRegistry:
    return ConnectionRegistry(
        connections=[
            ConnectionConfig(
                name="main-postgres",
                provider="postgres",
                settings={"dsn": "postgresql://localhost:5432/devmirror"},
            ),
        ],
    )
