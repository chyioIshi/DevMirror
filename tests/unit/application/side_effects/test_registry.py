import pytest

from app.application.exceptions import (
    SideEffectProviderAlreadyRegisteredError,
    SideEffectProviderNotFoundError,
)
from app.application.side_effects import SideEffectProviderRegistry
from app.domain.mocks.models import SideEffect, SideEffectContext, SideEffectType
from tests.testkit.fakes.application import FakeSideEffectProvider


class TestSideEffectProviderRegistry:
    """Checks side effect provider registry behavior."""

    def test_registers_and_returns_provider_by_name(self) -> None:
        provider = FakeSideEffectProvider(provider="fake")
        registry = SideEffectProviderRegistry()

        registry.register(provider)

        assert registry.get("fake") is provider

    def test_register_rejects_duplicate_provider(self) -> None:
        registry = SideEffectProviderRegistry()
        registry.register(FakeSideEffectProvider(provider="fake"))

        with pytest.raises(SideEffectProviderAlreadyRegisteredError) as exc_info:
            registry.register(FakeSideEffectProvider(provider="fake"))

        assert exc_info.value.details == {"provider": "fake"}

    def test_get_rejects_unknown_provider(self) -> None:
        registry = SideEffectProviderRegistry()

        with pytest.raises(SideEffectProviderNotFoundError) as exc_info:
            registry.get("missing")

        assert exc_info.value.details == {"provider": "missing"}

    @pytest.mark.asyncio
    async def test_fake_provider_executes_side_effect(self) -> None:
        provider = FakeSideEffectProvider(provider="fake")
        effect = SideEffect(
            type=SideEffectType.MESSAGE_PUBLISH,
            provider="fake",
            target={"topic": "events"},
            payload_template={"ok": True},
        )
        context = SideEffectContext(execution={"request_id": "request-1"})

        result = await provider.execute(effect, context)

        assert result.provider == "fake"
        assert result.success is True
        assert result.details == {"executions": 1}
        assert provider.executions == [(effect, context)]
