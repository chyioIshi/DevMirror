from dataclasses import dataclass, field
from typing import Any

from app.domain.mocks.models import (
    SideEffect,
    SideEffectContext,
    SideEffectExecutionStrategy,
    SideEffectMode,
    SideEffectType,
)
from app.infra.celery.routing import CeleryQueueRouter
from app.infra.celery.task_names import (
    SIDE_EFFECT_DISPATCH_TASK_NAME,
    SIDE_EFFECTS_BATCH_DISPATCH_TASK_NAME,
)
from app.infra.side_effects.schedulers import CeleryAsyncTaskScheduler


@dataclass(slots=True)
class FakeAsyncResult:
    id: str = "task-1"


@dataclass(slots=True)
class FakeCeleryApp:
    send_task_calls: list[dict[str, Any]] = field(default_factory=list)

    def send_task(
        self,
        name: str,
        args: list[Any],
        queue: str,
    ) -> FakeAsyncResult:
        self.send_task_calls.append({"name": name, "args": args, "queue": queue})
        return FakeAsyncResult()


class TestCeleryAsyncTaskScheduler:
    def test_schedules_side_effects_with_serialized_payload(self) -> None:
        celery_app = FakeCeleryApp()
        scheduler = CeleryAsyncTaskScheduler(app=celery_app)
        side_effect = SideEffect(
            type=SideEffectType.MESSAGE_PUBLISH,
            provider="kafka",
            target={"topic": "events"},
            payload_template={"ok": True},
            mode=SideEffectMode.ASYNC,
        )
        context = SideEffectContext(
            request={"path": "/orders"},
            mock={"id": "mock-1"},
            response={"status_code": 200},
            execution={"request_id": "request-1"},
        )

        scheduler.schedule_side_effects([side_effect], context)

        assert celery_app.send_task_calls == [
            {
                "name": SIDE_EFFECT_DISPATCH_TASK_NAME,
                "args": [
                    {
                        "side_effect": {
                            "type": "message_publish",
                            "provider": "kafka",
                            "target": {"topic": "events"},
                            "payload_template": {"ok": True},
                            "options": {},
                            "mode": "async",
                            "fail_policy": "ignore",
                            "execution_strategy": "parallel",
                            "enabled": True,
                        },
                        "context": {
                            "request": {"path": "/orders"},
                            "mock": {"id": "mock-1"},
                            "response": {"status_code": 200},
                            "execution": {"request_id": "request-1"},
                        },
                    }
                ],
                "queue": "side_effects.kafka",
            }
        ]

    def test_schedules_parallel_side_effects_as_separate_tasks(self) -> None:
        celery_app = FakeCeleryApp()
        scheduler = CeleryAsyncTaskScheduler(app=celery_app)
        side_effects = [
            SideEffect(
                type=SideEffectType.MESSAGE_PUBLISH,
                provider="kafka",
                target={"topic": "events"},
                payload_template={"index": 1},
                mode=SideEffectMode.ASYNC,
            ),
            SideEffect(
                type=SideEffectType.MESSAGE_PUBLISH,
                provider="rabbitmq",
                target={"routing_key": "mock.served"},
                payload_template={"index": 2},
                mode=SideEffectMode.ASYNC,
            ),
        ]
        context = SideEffectContext(execution={"request_id": "request-1"})

        scheduler.schedule_side_effects(side_effects, context)

        assert [call["name"] for call in celery_app.send_task_calls] == [
            SIDE_EFFECT_DISPATCH_TASK_NAME,
            SIDE_EFFECT_DISPATCH_TASK_NAME,
        ]
        assert [
            call["args"][0]["side_effect"]["provider"] for call in celery_app.send_task_calls
        ] == [
            "kafka",
            "rabbitmq",
        ]
        assert [call["queue"] for call in celery_app.send_task_calls] == [
            "side_effects.kafka",
            "side_effects.kafka",
        ]

    def test_schedules_sequential_side_effects_as_one_batch_task(self) -> None:
        celery_app = FakeCeleryApp()
        scheduler = CeleryAsyncTaskScheduler(app=celery_app)
        side_effects = [
            SideEffect(
                type=SideEffectType.DB_INSERT,
                provider="mongo",
                target={"collection": "events"},
                payload_template={"index": 1},
                mode=SideEffectMode.ASYNC,
                execution_strategy=SideEffectExecutionStrategy.SEQUENTIAL,
            ),
            SideEffect(
                type=SideEffectType.DB_UPDATE,
                provider="postgres",
                target={"table": "events"},
                payload_template={"index": 2},
                mode=SideEffectMode.ASYNC,
                execution_strategy=SideEffectExecutionStrategy.SEQUENTIAL,
            ),
        ]
        context = SideEffectContext(execution={"request_id": "request-1"})

        scheduler.schedule_side_effects(side_effects, context)

        assert celery_app.send_task_calls == [
            {
                "name": SIDE_EFFECTS_BATCH_DISPATCH_TASK_NAME,
                "args": [
                    {
                        "side_effects": [
                            {
                                "type": "db_insert",
                                "provider": "mongo",
                                "target": {"collection": "events"},
                                "payload_template": {"index": 1},
                                "options": {},
                                "mode": "async",
                                "fail_policy": "ignore",
                                "execution_strategy": "sequential",
                                "enabled": True,
                            },
                            {
                                "type": "db_update",
                                "provider": "postgres",
                                "target": {"table": "events"},
                                "payload_template": {"index": 2},
                                "options": {},
                                "mode": "async",
                                "fail_policy": "ignore",
                                "execution_strategy": "sequential",
                                "enabled": True,
                            },
                        ],
                        "context": {
                            "request": {},
                            "mock": {},
                            "response": {},
                            "execution": {"request_id": "request-1"},
                        },
                    }
                ],
                "queue": "side_effects.db",
            }
        ]

    def test_schedules_parallel_before_one_sequential_batch(self) -> None:
        celery_app = FakeCeleryApp()
        scheduler = CeleryAsyncTaskScheduler(app=celery_app)
        side_effects = [
            SideEffect(
                type=SideEffectType.MESSAGE_PUBLISH,
                provider="kafka",
                target={"topic": "events"},
                payload_template={"index": 1},
                execution_strategy=SideEffectExecutionStrategy.PARALLEL,
            ),
            SideEffect(
                type=SideEffectType.HTTP_CALLBACK,
                provider="http",
                target={"connection": "callback"},
                payload_template={"index": 2},
                execution_strategy=SideEffectExecutionStrategy.SEQUENTIAL,
            ),
        ]

        scheduler.schedule_side_effects(side_effects, SideEffectContext())

        assert [call["name"] for call in celery_app.send_task_calls] == [
            SIDE_EFFECT_DISPATCH_TASK_NAME,
            SIDE_EFFECTS_BATCH_DISPATCH_TASK_NAME,
        ]
        assert [call["queue"] for call in celery_app.send_task_calls] == [
            "side_effects.kafka",
            "side_effects.http",
        ]

    def test_uses_router_fallback_for_unknown_side_effect_type(self) -> None:
        celery_app = FakeCeleryApp()
        scheduler = CeleryAsyncTaskScheduler(
            app=celery_app,
            queue_router=CeleryQueueRouter(default_queue="custom.default"),
        )
        side_effect = SideEffect(
            type=SideEffectType.REDIS_SET,
            provider="redis",
            target={"key": "mock:last"},
            payload_template={"value": "ok"},
        )

        scheduler.schedule_side_effects([side_effect], SideEffectContext())

        assert celery_app.send_task_calls[0]["queue"] == "custom.default"
