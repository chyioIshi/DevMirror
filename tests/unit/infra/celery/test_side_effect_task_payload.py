from app.domain.mocks.models import (
    SideEffect,
    SideEffectContext,
    SideEffectExecutionStrategy,
    SideEffectFailPolicy,
    SideEffectMode,
    SideEffectType,
)
from app.infra.celery.task_payload import (
    DispatchSideEffectsBatchTaskPayload,
    DispatchSideEffectTaskPayload,
)


class TestSideEffectTaskPayload:
    def test_payload_round_trip(self) -> None:
        side_effect = SideEffect(
            type=SideEffectType.MESSAGE_PUBLISH,
            provider="rabbitmq",
            target={"routing_key": "mock.served"},
            payload_template={"ok": True},
            options={"max_attempts": 2},
            mode=SideEffectMode.ASYNC,
            fail_policy=SideEffectFailPolicy.RETRY,
            execution_strategy=SideEffectExecutionStrategy.SEQUENTIAL,
            enabled=False,
        )
        context = SideEffectContext(
            request={"path": "/orders"},
            mock={"id": "mock-1"},
            response={"status_code": 200},
            execution={"request_id": "request-1"},
        )

        payload = DispatchSideEffectTaskPayload.from_domain(side_effect, context)
        raw_payload = payload.model_dump(mode="json")
        result = DispatchSideEffectTaskPayload.model_validate(raw_payload)

        assert result.to_side_effect() == side_effect
        assert result.to_context() == context

    def test_batch_payload_round_trip(self) -> None:
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
        raw_payload = payload.model_dump(mode="json")
        result = DispatchSideEffectsBatchTaskPayload.model_validate(raw_payload)

        assert result.to_side_effects() == side_effects
        assert result.to_context() == context
