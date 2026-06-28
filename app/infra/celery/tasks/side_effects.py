"""Celery task for side effect execution."""

import asyncio
import logging
from typing import Any

from app.domain.mocks.models import (
    SideEffect,
    SideEffectContext,
    SideEffectExecutionResult,
)
from app.infra.celery.app import celery_app
from app.infra.celery.state import WorkerState
from app.infra.celery.task_names import (
    SIDE_EFFECT_DISPATCH_TASK_NAME,
    SIDE_EFFECTS_BATCH_DISPATCH_TASK_NAME,
)
from app.infra.celery.task_payload import (
    DispatchSideEffectsBatchTaskPayload,
    DispatchSideEffectTaskPayload,
)

logger = logging.getLogger(__name__)


@celery_app.task(
    name=SIDE_EFFECT_DISPATCH_TASK_NAME,
    acks_late=True,
    ignore_result=True,
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
)
def dispatch_side_effect_task(
    payload: dict[str, Any],
) -> dict[str, Any] | None:
    """Dispatch one side effect in a Celery worker."""
    return asyncio.run(_dispatch_side_effect(payload))


@celery_app.task(
    name=SIDE_EFFECTS_BATCH_DISPATCH_TASK_NAME,
    acks_late=True,
    ignore_result=True,
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
)
def dispatch_side_effects_batch_task(
    payload: dict[str, Any],
) -> list[dict[str, Any]]:
    """Dispatch an ordered side effect batch in a Celery worker."""
    return asyncio.run(_dispatch_side_effects_batch(payload))


async def _dispatch_side_effect(payload: dict[str, Any]) -> dict[str, Any] | None:
    task_payload = DispatchSideEffectTaskPayload.model_validate(payload)
    side_effect = task_payload.to_side_effect()
    context = task_payload.to_context()
    container = WorkerState.get_container()
    try:
        result = await container.side_effect_dispatcher_service.dispatch_one(
            side_effect,
            context,
        )
    except Exception:
        _log_task_outcome(side_effect=side_effect, context=context, status="failed")
        raise

    if result is None:
        return None

    _log_task_result(side_effect=side_effect, context=context, result=result)
    return result.to_mapping()


async def _dispatch_side_effects_batch(payload: dict[str, Any]) -> list[dict[str, Any]]:
    task_payload = DispatchSideEffectsBatchTaskPayload.model_validate(payload)
    side_effects = task_payload.to_side_effects()
    context = task_payload.to_context()
    container = WorkerState.get_container()
    try:
        results = await container.side_effect_dispatcher_service.dispatch(
            side_effects,
            context,
        )
    except Exception:
        _log_batch_task_outcome(side_effects=side_effects, context=context, status="failed")
        raise

    _log_batch_task_result(side_effects=side_effects, context=context, result_count=len(results))
    return [result.to_mapping() for result in results]


def _log_task_result(
    *,
    side_effect: SideEffect,
    context: SideEffectContext,
    result: SideEffectExecutionResult,
) -> None:
    log = logger.info if result.success else logger.error
    log(
        "side_effect_celery_task_finished",
        extra={
            "request_id": context.execution.get("request_id"),
            "mock_id": context.mock.get("id"),
            "side_effect_type": side_effect.type,
            "provider": result.provider,
            "success": result.success,
            "details": result.details,
            "error": result.error,
        },
    )


def _log_batch_task_result(
    *,
    side_effects: list[SideEffect],
    context: SideEffectContext,
    result_count: int,
) -> None:
    logger.info(
        "side_effect_celery_batch_task_finished",
        extra={
            "request_id": context.execution.get("request_id"),
            "mock_id": context.mock.get("id"),
            "side_effect_type": [side_effect.type for side_effect in side_effects],
            "provider": [side_effect.provider for side_effect in side_effects],
            "execution_strategy": [side_effect.execution_strategy for side_effect in side_effects],
            "result_count": result_count,
            "status": "finished",
        },
    )


def _log_task_outcome(
    *,
    side_effect: SideEffect,
    context: SideEffectContext,
    status: str,
) -> None:
    log = logger.error if status == "failed" else logger.info
    log(
        "side_effect_celery_task_finished",
        extra={
            "request_id": context.execution.get("request_id"),
            "mock_id": context.mock.get("id"),
            "side_effect_type": side_effect.type,
            "provider": side_effect.provider,
            "status": status,
        },
    )


def _log_batch_task_outcome(
    *,
    side_effects: list[SideEffect],
    context: SideEffectContext,
    status: str,
) -> None:
    log = logger.error if status == "failed" else logger.info
    log(
        "side_effect_celery_batch_task_finished",
        extra={
            "request_id": context.execution.get("request_id"),
            "mock_id": context.mock.get("id"),
            "side_effect_type": [side_effect.type for side_effect in side_effects],
            "provider": [side_effect.provider for side_effect in side_effects],
            "execution_strategy": [side_effect.execution_strategy for side_effect in side_effects],
            "status": status,
        },
    )
