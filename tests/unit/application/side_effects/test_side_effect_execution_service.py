import pytest

from app.application.exceptions import SideEffectExecutionFailedError
from app.application.side_effects import (
    SideEffectDispatcherService,
    SideEffectExecutionService,
    SideEffectProviderRegistry,
)
from app.domain.mocks.models import (
    SideEffect,
    SideEffectExecutionResult,
    SideEffectFailPolicy,
    SideEffectMode,
    SideEffectType,
)
from tests.testkit.fakes.application import (
    FakeAsyncTaskScheduler,
    FakeSideEffectDispatcherService,
    FakeSideEffectProvider,
)


class TestSideEffectExecutionService:
    @pytest.mark.asyncio
    async def test_skips_empty_side_effects(
        self,
        mock_factory,
        request_factory,
    ) -> None:
        mock = mock_factory.create_mock()
        service, dispatcher, _ = self._service()

        await service.execute(
            side_effects=[],
            request=request_factory.create_request_context(),
            mock=mock,
            response=mock.response,
        )

        assert dispatcher.dispatch_calls == []

    @pytest.mark.asyncio
    async def test_sync_side_effect_triggers_dispatcher(
        self,
        mock_factory,
        request_factory,
    ) -> None:
        side_effect = self._message_side_effect(mode=SideEffectMode.SYNC)
        mock = mock_factory.create_mock(response_side_effects=[side_effect])
        request_context = request_factory.create_request_context()
        service, dispatcher, _ = self._service()

        await service.execute(
            side_effects=mock.response.side_effects,
            request=request_context,
            mock=mock,
            response=mock.response,
        )

        assert len(dispatcher.dispatch_calls) == 1
        side_effects, context = dispatcher.dispatch_calls[0]
        assert side_effects == [side_effect]
        assert context.execution == {"request_id": request_context.id}

    @pytest.mark.asyncio
    async def test_async_side_effect_is_scheduled(
        self,
        mock_factory,
        request_factory,
    ) -> None:
        side_effect = self._message_side_effect(mode=SideEffectMode.ASYNC)
        mock = mock_factory.create_mock(response_side_effects=[side_effect])
        service, dispatcher, scheduler = self._service()

        await service.execute(
            side_effects=mock.response.side_effects,
            request=request_factory.create_request_context(),
            mock=mock,
            response=mock.response,
        )

        assert dispatcher.dispatch_calls == []
        assert len(scheduler.scheduled) == 1
        assert scheduler.scheduled[0].side_effects == [side_effect]

    @pytest.mark.asyncio
    async def test_disabled_async_side_effect_does_not_break_execution(
        self,
        mock_factory,
        request_factory,
    ) -> None:
        side_effect = self._message_side_effect(
            mode=SideEffectMode.ASYNC,
            enabled=False,
        )
        mock = mock_factory.create_mock(response_side_effects=[side_effect])
        service, dispatcher, scheduler = self._service()

        await service.execute(
            side_effects=mock.response.side_effects,
            request=request_factory.create_request_context(),
            mock=mock,
            response=mock.response,
        )

        assert dispatcher.dispatch_calls == []
        assert len(scheduler.scheduled) == 1
        assert scheduler.scheduled[0].side_effects == [side_effect]

    @pytest.mark.asyncio
    async def test_ignore_fail_policy_does_not_raise(
        self,
        mock_factory,
        request_factory,
    ) -> None:
        side_effect = self._message_side_effect(
            mode=SideEffectMode.SYNC,
            fail_policy=SideEffectFailPolicy.IGNORE,
        )
        provider = FakeSideEffectProvider(
            provider="fake",
            results=[
                SideEffectExecutionResult(
                    provider="fake",
                    success=False,
                    error="failed",
                ),
            ],
        )
        service = self._service_with_real_dispatcher(provider=provider)
        mock = mock_factory.create_mock(response_side_effects=[side_effect])

        await service.execute(
            side_effects=mock.response.side_effects,
            request=request_factory.create_request_context(),
            mock=mock,
            response=mock.response,
        )

        assert len(provider.executions) == 1

    @pytest.mark.asyncio
    async def test_fail_mock_fail_policy_raises_application_error(
        self,
        mock_factory,
        request_factory,
    ) -> None:
        side_effect = self._message_side_effect(
            mode=SideEffectMode.SYNC,
            fail_policy=SideEffectFailPolicy.FAIL_MOCK,
        )
        provider = FakeSideEffectProvider(
            provider="fake",
            results=[
                SideEffectExecutionResult(
                    provider="fake",
                    success=False,
                    error="failed",
                ),
            ],
        )
        service = self._service_with_real_dispatcher(provider=provider)
        mock = mock_factory.create_mock(response_side_effects=[side_effect])

        with pytest.raises(SideEffectExecutionFailedError):
            await service.execute(
                side_effects=mock.response.side_effects,
                request=request_factory.create_request_context(),
                mock=mock,
                response=mock.response,
            )

    def _service(
        self,
    ) -> tuple[
        SideEffectExecutionService,
        FakeSideEffectDispatcherService,
        FakeAsyncTaskScheduler,
    ]:
        dispatcher = FakeSideEffectDispatcherService()
        scheduler = FakeAsyncTaskScheduler()
        return (
            SideEffectExecutionService(
                dispatcher_service=dispatcher,
                async_task_scheduler=scheduler,
            ),
            dispatcher,
            scheduler,
        )

    def _service_with_real_dispatcher(
        self,
        *,
        provider: FakeSideEffectProvider,
    ) -> SideEffectExecutionService:
        registry = SideEffectProviderRegistry()
        registry.register(provider)
        return SideEffectExecutionService(
            dispatcher_service=SideEffectDispatcherService(registry=registry),
            async_task_scheduler=FakeAsyncTaskScheduler(),
        )

    def _message_side_effect(
        self,
        *,
        mode: SideEffectMode,
        fail_policy: SideEffectFailPolicy = SideEffectFailPolicy.IGNORE,
        enabled: bool = True,
    ) -> SideEffect:
        return SideEffect(
            type=SideEffectType.MESSAGE_PUBLISH,
            provider="fake",
            target={"topic": "events"},
            payload_template={"ok": True},
            mode=mode,
            fail_policy=fail_policy,
            enabled=enabled,
        )
