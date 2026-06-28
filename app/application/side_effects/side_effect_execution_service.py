"""Application service for executing mock response side effects."""

from collections.abc import Sequence
from typing import Any

from app.application.side_effects.side_effect_dispatcher_service import (
    SideEffectDispatcherService,
)
from app.domain.mocks.models import (
    Mock,
    MockResponse,
    SideEffect,
    SideEffectContext,
    SideEffectMode,
)
from app.domain.mocks.ports import AsyncTaskScheduler
from app.domain.request_contexts import RequestContext


class SideEffectExecutionService:
    """Builds side effect context and coordinates sync/async execution."""

    def __init__(
        self,
        *,
        dispatcher_service: SideEffectDispatcherService,
        async_task_scheduler: AsyncTaskScheduler,
    ) -> None:
        """Initializes the side effect execution service."""
        self._dispatcher_service = dispatcher_service
        self._async_task_scheduler = async_task_scheduler

    async def execute(
        self,
        *,
        side_effects: Sequence[SideEffect],
        request: RequestContext,
        mock: Mock,
        response: MockResponse,
        execution: dict[str, Any] | None = None,
    ) -> None:
        """Executes side effects declared by a resolved mock response."""
        if not side_effects:
            return

        context = SideEffectContext.from_domain(
            request=request,
            mock=mock,
            response=response,
            execution=self._execution_metadata(request, execution),
        )
        await self._dispatch_sync_side_effects(side_effects, context)
        self._schedule_async_side_effects(side_effects, context)

    async def _dispatch_sync_side_effects(
        self,
        side_effects: Sequence[SideEffect],
        context: SideEffectContext,
    ) -> None:
        sync_side_effects = [
            side_effect for side_effect in side_effects if side_effect.mode == SideEffectMode.SYNC
        ]
        if not sync_side_effects:
            return

        await self._dispatcher_service.dispatch(sync_side_effects, context)

    def _schedule_async_side_effects(
        self,
        side_effects: Sequence[SideEffect],
        context: SideEffectContext,
    ) -> None:
        async_side_effects = [
            side_effect for side_effect in side_effects if side_effect.mode == SideEffectMode.ASYNC
        ]
        if not async_side_effects:
            return

        self._async_task_scheduler.schedule_side_effects(async_side_effects, context)

    def _execution_metadata(
        self,
        request_context: RequestContext,
        execution: dict[str, Any] | None,
    ) -> dict[str, Any]:
        metadata = {"request_id": request_context.id}
        metadata.update(execution or {})
        return metadata
