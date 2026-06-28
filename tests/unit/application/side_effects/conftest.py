import pytest

from app.application.side_effects import SideEffectDispatcherService, SideEffectProviderRegistry
from app.domain.mocks.models import SideEffect, SideEffectContext, SideEffectType
from tests.testkit.fakes.application import FakeSideEffectProvider


@pytest.fixture
def side_effect_context() -> SideEffectContext:
    return SideEffectContext(
        request={
            "body": {
                "dealId": "deal-1",
                "items": [{"id": "item-1"}],
            },
            "headers": {"a-customerid": "customer-1"},
            "query": {"customerId": "query-customer-1"},
        },
        mock={"id": "mock-1"},
        response={"status_code": 202},
        execution={"request_id": "request-1"},
    )


@pytest.fixture
def fake_side_effect_provider() -> FakeSideEffectProvider:
    return FakeSideEffectProvider(provider="fake")


@pytest.fixture
def side_effect_registry(
    fake_side_effect_provider: FakeSideEffectProvider,
) -> SideEffectProviderRegistry:
    registry = SideEffectProviderRegistry()
    registry.register(fake_side_effect_provider)
    return registry


@pytest.fixture
def side_effect_dispatcher(
    side_effect_registry: SideEffectProviderRegistry,
) -> SideEffectDispatcherService:
    return SideEffectDispatcherService(registry=side_effect_registry)


@pytest.fixture
def side_effect() -> SideEffect:
    return SideEffect(
        type=SideEffectType.MESSAGE_PUBLISH,
        provider="fake",
        target={"topic": "events"},
        payload_template={"ok": True},
    )
