"""In-process async side effect scheduling adapter."""

import asyncio
import logging
from collections.abc import Sequence

from app.domain.mocks.models import SideEffect, SideEffectContext
from app.domain.mocks.ports import SideEffectDispatcher

logger = logging.getLogger(__name__)


class InProcessAsyncTaskScheduler:
    """Schedules background tasks in the current Python process."""

    def __init__(self, dispatcher: SideEffectDispatcher) -> None:
        """Initializes the scheduler with the dispatcher used by background tasks."""
        self._dispatcher = dispatcher

    def schedule_side_effects(
        self,
        side_effects: Sequence[SideEffect],
        context: SideEffectContext,
    ) -> None:
        """Schedule side effect dispatch through the current asyncio event loop."""
        task = asyncio.create_task(self._dispatcher.dispatch(list(side_effects), context))
        task.add_done_callback(self._log_background_task_error)

    def _log_background_task_error(
        self,
        task: asyncio.Task[object],
    ) -> None:
        try:
            task.result()
        except Exception:
            logger.exception("Async side effect dispatch failed")
