import logging
from dataclasses import dataclass, field

from app.domain.mocks.models import (
    SideEffect,
    SideEffectContext,
    SideEffectExecutionResult,
    SideEffectExecutionStrategy,
    SideEffectType,
)
from app.infra.celery.task_payload import (
    DispatchSideEffectsBatchTaskPayload,
    DispatchSideEffectTaskPayload,
)
from app.infra.celery.tasks.side_effects import (
    _dispatch_side_effect,
    _dispatch_side_effects_batch,
)


@dataclass(slots=True)
class FakeSideEffectDispatcherService:
    dispatch_calls: list[tuple[list[SideEffect], SideEffectContext]] = field(
        default_factory=list,
    )
    dispatch_one_calls: list[tuple[SideEffect, SideEffectContext]] = field(
        default_factory=list,
    )
    results: list[SideEffectExecutionResult] = field(default_factory=list)
    result: SideEffectExecutionResult | None = None

    async def dispatch(
        self,
        side_effects: list[SideEffect],
        context: SideEffectContext,
    ) -> list[SideEffectExecutionResult]:
        self.dispatch_calls.append((side_effects, context))
        return self.results

    async def dispatch_one(
        self,
        side_effect: SideEffect,
        context: SideEffectContext,
    ) -> SideEffectExecutionResult | None:
        self.dispatch_one_calls.append((side_effect, context))
        return self.result


@dataclass(slots=True)
class FakeContainer:
    side_effect_dispatcher_service: FakeSideEffectDispatcherService = field(
        default_factory=FakeSideEffectDispatcherService,
    )
    closed: bool = False

    async def aclose(self) -> None:
        self.closed = True


class TestSideEffectTasks:
    async def test_execute_side_effect_dispatches_payload_through_worker_container(
        self,
        monkeypatch,
    ) -> None:
        container = FakeContainer()
        side_effect = SideEffect(
            type=SideEffectType.MESSAGE_PUBLISH,
            provider="kafka",
            target={"topic": "events"},
            payload_template={"ok": True},
        )
        context = SideEffectContext(execution={"request_id": "request-1"})
        monkeypatch.setattr(
            "app.infra.celery.tasks.side_effects.WorkerState.get_container",
            lambda: container,
        )

        payload = DispatchSideEffectTaskPayload.from_domain(
            side_effect,
            context,
        )

        await _dispatch_side_effect(payload.model_dump(mode="json"))

        assert container.side_effect_dispatcher_service.dispatch_calls == []
        assert container.side_effect_dispatcher_service.dispatch_one_calls == [
            (side_effect, context)
        ]
        assert container.closed is False

    async def test_execute_side_effect_returns_serialized_result(
        self,
        monkeypatch,
    ) -> None:
        result = SideEffectExecutionResult(
            provider="kafka",
            success=True,
            details={"topic": "events"},
        )
        container = FakeContainer(
            side_effect_dispatcher_service=FakeSideEffectDispatcherService(
                result=result,
            ),
        )
        side_effect = SideEffect(
            type=SideEffectType.MESSAGE_PUBLISH,
            provider="kafka",
            target={"topic": "events"},
            payload_template={"ok": True},
        )
        context = SideEffectContext(execution={"request_id": "request-1"})
        payload = DispatchSideEffectTaskPayload.from_domain(side_effect, context)
        monkeypatch.setattr(
            "app.infra.celery.tasks.side_effects.WorkerState.get_container",
            lambda: container,
        )

        serialized_result = await _dispatch_side_effect(payload.model_dump(mode="json"))

        assert serialized_result == {
            "provider": "kafka",
            "success": True,
            "details": {"topic": "events"},
            "error": None,
        }

    async def test_execute_side_effects_logs_actual_result(
        self,
        monkeypatch,
        caplog,
    ) -> None:
        result = SideEffectExecutionResult(
            provider="kafka",
            success=False,
            details={"topic": "events"},
            error="publish failed",
        )
        container = FakeContainer(
            side_effect_dispatcher_service=FakeSideEffectDispatcherService(
                result=result,
            ),
        )
        side_effect = SideEffect(
            type=SideEffectType.MESSAGE_PUBLISH,
            provider="kafka",
            target={"topic": "events"},
            payload_template={"ok": True},
        )
        context = SideEffectContext(
            mock={"id": "mock-1"},
            execution={"request_id": "request-1"},
        )
        payload = DispatchSideEffectTaskPayload.from_domain(side_effect, context)
        monkeypatch.setattr(
            "app.infra.celery.tasks.side_effects.WorkerState.get_container",
            lambda: container,
        )

        with caplog.at_level(logging.ERROR):
            await _dispatch_side_effect(payload.model_dump(mode="json"))

        record = next(
            item for item in caplog.records if item.message == "side_effect_celery_task_finished"
        )
        assert record.request_id == "request-1"
        assert record.mock_id == "mock-1"
        assert record.side_effect_type == SideEffectType.MESSAGE_PUBLISH
        assert record.provider == "kafka"
        assert record.success is False
        assert record.details == {"topic": "events"}
        assert record.error == "publish failed"

    async def test_execute_side_effects_batch_dispatches_ordered_payload(
        self,
        monkeypatch,
    ) -> None:
        results = [
            SideEffectExecutionResult(provider="kafka", success=True),
            SideEffectExecutionResult(provider="http", success=True),
        ]
        container = FakeContainer(
            side_effect_dispatcher_service=FakeSideEffectDispatcherService(
                results=results,
            ),
        )
        side_effects = [
            SideEffect(
                type=SideEffectType.MESSAGE_PUBLISH,
                provider="kafka",
                target={"topic": "events"},
                payload_template={"index": 1},
                execution_strategy=SideEffectExecutionStrategy.SEQUENTIAL,
            ),
            SideEffect(
                type=SideEffectType.HTTP_CALLBACK,
                provider="http",
                target={"connection": "callback"},
                payload_template={"index": 2},
                execution_strategy=SideEffectExecutionStrategy.SEQUENTIAL,
            ),
        ]
        context = SideEffectContext(execution={"request_id": "request-1"})
        payload = DispatchSideEffectsBatchTaskPayload.from_domain(side_effects, context)
        monkeypatch.setattr(
            "app.infra.celery.tasks.side_effects.WorkerState.get_container",
            lambda: container,
        )

        serialized_results = await _dispatch_side_effects_batch(
            payload.model_dump(mode="json"),
        )

        assert container.side_effect_dispatcher_service.dispatch_calls == [(side_effects, context)]
        assert container.side_effect_dispatcher_service.dispatch_one_calls == []
        assert serialized_results == [result.to_mapping() for result in results]
