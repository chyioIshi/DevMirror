import pytest

from app.domain.mocks.models import SideEffectContext
from app.infra.side_effects import ConnectionConfig, ConnectionRegistry


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
