import pytest

from app.application.exceptions import (
    SideEffectExecutionFailedError,
    SideEffectProviderNotFoundError,
)
from app.application.side_effects import SideEffectDispatcherService, SideEffectProviderRegistry
from app.domain.mocks.models import (
    SideEffect,
    SideEffectContext,
    SideEffectExecutionResult,
    SideEffectFailPolicy,
    SideEffectType,
)
from tests.testkit.fakes.application import FakeSideEffectProvider


class TestSideEffectDispatcherService:
    """Checks side effect dispatcher orchestration."""

    @pytest.mark.asyncio
    async def test_dispatch_calls_registered_provider(
        self,
        side_effect_dispatcher: SideEffectDispatcherService,
        fake_side_effect_provider: FakeSideEffectProvider,
        side_effect_context: SideEffectContext,
        side_effect: SideEffect,
    ) -> None:
        await side_effect_dispatcher.dispatch([side_effect], side_effect_context)

        assert len(fake_side_effect_provider.executions) == 1
        assert fake_side_effect_provider.executions[0] == (side_effect, side_effect_context)

    @pytest.mark.asyncio
    async def test_dispatch_uses_provider_matching_effect_provider(
        self,
        side_effect_context: SideEffectContext,
    ) -> None:
        fake_provider = FakeSideEffectProvider(provider="fake")
        other_provider = FakeSideEffectProvider(provider="other")
        registry = SideEffectProviderRegistry()
        registry.register(fake_provider)
        registry.register(other_provider)
        dispatcher = SideEffectDispatcherService(registry=registry)
        side_effect = SideEffect(
            type=SideEffectType.MESSAGE_PUBLISH,
            provider="other",
            target={"topic": "events"},
            payload_template={"ok": True},
        )

        await dispatcher.dispatch([side_effect], side_effect_context)

        assert fake_provider.executions == []
        assert len(other_provider.executions) == 1

    @pytest.mark.asyncio
    async def test_dispatch_skips_disabled_side_effect(
        self,
        side_effect_dispatcher: SideEffectDispatcherService,
        fake_side_effect_provider: FakeSideEffectProvider,
        side_effect_context: SideEffectContext,
    ) -> None:
        side_effect = SideEffect(
            type=SideEffectType.MESSAGE_PUBLISH,
            provider="fake",
            target={"topic": "events"},
            payload_template={"ok": True},
            enabled=False,
        )

        result = await side_effect_dispatcher.dispatch([side_effect], side_effect_context)

        assert result == []
        assert fake_side_effect_provider.executions == []

    @pytest.mark.asyncio
    async def test_dispatch_raises_clear_error_for_unknown_provider(
        self,
        side_effect_context: SideEffectContext,
        side_effect: SideEffect,
    ) -> None:
        dispatcher = SideEffectDispatcherService(registry=SideEffectProviderRegistry())

        with pytest.raises(SideEffectProviderNotFoundError) as exc_info:
            await dispatcher.dispatch([side_effect], side_effect_context)

        assert exc_info.value.details == {"provider": "fake"}

    @pytest.mark.asyncio
    async def test_ignore_fail_policy_does_not_raise(
        self,
        side_effect_dispatcher: SideEffectDispatcherService,
        fake_side_effect_provider: FakeSideEffectProvider,
        side_effect_context: SideEffectContext,
    ) -> None:
        fake_side_effect_provider.results.append(
            SideEffectExecutionResult(provider="fake", success=False, error="failed"),
        )
        side_effect = SideEffect(
            type=SideEffectType.MESSAGE_PUBLISH,
            provider="fake",
            target={"topic": "events"},
            payload_template={"ok": True},
            fail_policy=SideEffectFailPolicy.IGNORE,
        )

        result = await side_effect_dispatcher.dispatch([side_effect], side_effect_context)

        assert result == [
            SideEffectExecutionResult(provider="fake", success=False, error="failed"),
        ]

    @pytest.mark.asyncio
    async def test_fail_mock_fail_policy_raises(
        self,
        side_effect_dispatcher: SideEffectDispatcherService,
        fake_side_effect_provider: FakeSideEffectProvider,
        side_effect_context: SideEffectContext,
    ) -> None:
        fake_side_effect_provider.results.append(
            SideEffectExecutionResult(provider="fake", success=False, error="failed"),
        )
        side_effect = SideEffect(
            type=SideEffectType.MESSAGE_PUBLISH,
            provider="fake",
            target={"topic": "events"},
            payload_template={"ok": True},
            fail_policy=SideEffectFailPolicy.FAIL_MOCK,
        )

        with pytest.raises(SideEffectExecutionFailedError) as exc_info:
            await side_effect_dispatcher.dispatch([side_effect], side_effect_context)

        assert exc_info.value.details == {
            "provider": "fake",
            "attempts": 1,
            "error": "failed",
            "details": {},
        }

    @pytest.mark.asyncio
    async def test_retry_fail_policy_performs_multiple_attempts(
        self,
        side_effect_dispatcher: SideEffectDispatcherService,
        fake_side_effect_provider: FakeSideEffectProvider,
        side_effect_context: SideEffectContext,
    ) -> None:
        fake_side_effect_provider.results.extend(
            [
                SideEffectExecutionResult(provider="fake", success=False, error="failed-1"),
                SideEffectExecutionResult(provider="fake", success=False, error="failed-2"),
                SideEffectExecutionResult(provider="fake", success=True),
            ],
        )
        side_effect = SideEffect(
            type=SideEffectType.MESSAGE_PUBLISH,
            provider="fake",
            target={"topic": "events"},
            payload_template={"ok": True},
            options={"max_attempts": 3},
            fail_policy=SideEffectFailPolicy.RETRY,
        )

        result = await side_effect_dispatcher.dispatch([side_effect], side_effect_context)

        assert len(fake_side_effect_provider.executions) == 3
        assert result == [SideEffectExecutionResult(provider="fake", success=True)]

    @pytest.mark.asyncio
    async def test_dispatch_renders_payload_template_before_execution(
        self,
        side_effect_dispatcher: SideEffectDispatcherService,
        fake_side_effect_provider: FakeSideEffectProvider,
        side_effect_context: SideEffectContext,
    ) -> None:
        side_effect = SideEffect(
            type=SideEffectType.MESSAGE_PUBLISH,
            provider="fake",
            target={"topic": "events"},
            payload_template={"id": "{{request.body.dealId}}"},
        )

        await side_effect_dispatcher.dispatch([side_effect], side_effect_context)

        executed_effect = fake_side_effect_provider.executions[0][0]
        assert executed_effect.payload_template == {"id": "deal-1"}

    @pytest.mark.asyncio
    async def test_dispatch_renders_options_before_execution(
        self,
        side_effect_dispatcher: SideEffectDispatcherService,
        fake_side_effect_provider: FakeSideEffectProvider,
        side_effect_context: SideEffectContext,
    ) -> None:
        side_effect = SideEffect(
            type=SideEffectType.MESSAGE_PUBLISH,
            provider="fake",
            target={"topic": "events"},
            payload_template={"ok": True},
            options={"request_id": "{{execution.request_id}}"},
        )

        await side_effect_dispatcher.dispatch([side_effect], side_effect_context)

        executed_effect = fake_side_effect_provider.executions[0][0]
        assert executed_effect.options == {"request_id": "request-1"}

    @pytest.mark.asyncio
    async def test_dispatch_returns_execution_results(
        self,
        side_effect_dispatcher: SideEffectDispatcherService,
        fake_side_effect_provider: FakeSideEffectProvider,
        side_effect_context: SideEffectContext,
        side_effect: SideEffect,
    ) -> None:
        fake_side_effect_provider.results.append(
            SideEffectExecutionResult(
                provider="fake",
                success=True,
                details={"sent": True},
            ),
        )

        result = await side_effect_dispatcher.dispatch([side_effect], side_effect_context)

        assert result == [
            SideEffectExecutionResult(
                provider="fake",
                success=True,
                details={"sent": True},
            ),
        ]
