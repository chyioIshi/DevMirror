"""Celery-backed async side effect scheduling adapter."""

import logging
from collections.abc import Sequence
from typing import Any

from app.domain.mocks.models import (
    SideEffect,
    SideEffectContext,
    SideEffectExecutionStrategy,
)
from app.infra.celery.app import celery_app
from app.infra.celery.routing import CeleryQueueRouter
from app.infra.celery.task_names import (
    SIDE_EFFECT_DISPATCH_TASK_NAME,
    SIDE_EFFECTS_BATCH_DISPATCH_TASK_NAME,
)
from app.infra.celery.task_payload import (
    DispatchSideEffectsBatchTaskPayload,
    DispatchSideEffectTaskPayload,
)

logger = logging.getLogger(__name__)


class CeleryAsyncTaskScheduler:
    """Schedules side effect execution through Celery."""

    def __init__(
        self,
        *,
        queue: str | None = None,
        app: Any = celery_app,
        queue_router: CeleryQueueRouter | None = None,
    ) -> None:
        """Initializes the scheduler with the Celery app used to publish tasks."""
        self._app = app
        self._queue_router = queue_router or CeleryQueueRouter(
            default_queue=queue or "side_effects.default",
        )

    def schedule_side_effects(
        self,
        side_effects: Sequence[SideEffect],
        context: SideEffectContext,
    ) -> None:
        """Send side effect execution to the Celery broker."""
        parallel_side_effects, sequential_side_effects = self._split_by_strategy(side_effects)
        self._schedule_parallel(parallel_side_effects, context)
        self._schedule_sequential(sequential_side_effects, context)

    def _split_by_strategy(
        self,
        side_effects: Sequence[SideEffect],
    ) -> tuple[list[SideEffect], list[SideEffect]]:
        parallel_side_effects: list[SideEffect] = []
        sequential_side_effects: list[SideEffect] = []

        for side_effect in side_effects:
            if side_effect.execution_strategy == SideEffectExecutionStrategy.PARALLEL:
                parallel_side_effects.append(side_effect)
            else:
                sequential_side_effects.append(side_effect)

        return parallel_side_effects, sequential_side_effects

    def _schedule_parallel(
        self,
        side_effects: Sequence[SideEffect],
        context: SideEffectContext,
    ) -> None:
        for side_effect in side_effects:
            queue = self._queue_router.queue_for(side_effect)
            payload = DispatchSideEffectTaskPayload.from_domain(side_effect, context)
            result = self._send_task(
                task_name=SIDE_EFFECT_DISPATCH_TASK_NAME,
                payload=payload.model_dump(mode="json"),
                queue=queue,
            )
            self._log_scheduled_task(
                task_id=getattr(result, "id", None),
                task_name=SIDE_EFFECT_DISPATCH_TASK_NAME,
                queue=queue,
                context=context,
                side_effect=side_effect,
            )

    def _schedule_sequential(
        self,
        side_effects: Sequence[SideEffect],
        context: SideEffectContext,
    ) -> None:
        if not side_effects:
            return

        queue = self._queue_router.queue_for_batch(side_effects)
        payload = DispatchSideEffectsBatchTaskPayload.from_domain(list(side_effects), context)
        result = self._send_task(
            task_name=SIDE_EFFECTS_BATCH_DISPATCH_TASK_NAME,
            payload=payload.model_dump(mode="json"),
            queue=queue,
        )
        self._log_scheduled_batch_task(
            task_id=getattr(result, "id", None),
            queue=queue,
            context=context,
            side_effects=side_effects,
        )

    def _send_task(self, *, task_name: str, payload: dict[str, Any], queue: str) -> Any:
        return self._app.send_task(task_name, args=[payload], queue=queue)

    def _log_scheduled_task(
        self,
        *,
        task_id: str | None,
        task_name: str,
        queue: str,
        context: SideEffectContext,
        side_effect: SideEffect,
    ) -> None:
        logger.info(
            "side_effect_celery_task_scheduled",
            extra={
                "task_id": task_id,
                "task_name": task_name,
                "queue": queue,
                "request_id": context.execution.get("request_id"),
                "mock_id": context.mock.get("id"),
                "side_effect_type": side_effect.type,
                "provider": side_effect.provider,
                "execution_strategy": side_effect.execution_strategy,
            },
        )

    def _log_scheduled_batch_task(
        self,
        *,
        task_id: str | None,
        queue: str,
        context: SideEffectContext,
        side_effects: Sequence[SideEffect],
    ) -> None:
        logger.info(
            "side_effect_celery_batch_task_scheduled",
            extra={
                "task_id": task_id,
                "task_name": SIDE_EFFECTS_BATCH_DISPATCH_TASK_NAME,
                "queue": queue,
                "request_id": context.execution.get("request_id"),
                "mock_id": context.mock.get("id"),
                "side_effect_type": [side_effect.type for side_effect in side_effects],
                "provider": [side_effect.provider for side_effect in side_effects],
                "execution_strategy": SideEffectExecutionStrategy.SEQUENTIAL,
            },
        )
