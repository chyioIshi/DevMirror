"""In-process async task scheduling adapter."""

import asyncio
import logging
from collections.abc import Coroutine
from typing import Any

logger = logging.getLogger(__name__)


class InProcessAsyncTaskScheduler:
    """Schedules background tasks in the current Python process."""

    def schedule(self, coroutine: Coroutine[Any, Any, None]) -> None:
        """Schedule coroutine execution through the current asyncio event loop."""
        task = asyncio.create_task(coroutine)
        task.add_done_callback(self._log_background_task_error)

    def _log_background_task_error(self, task: asyncio.Task[None]) -> None:
        try:
            task.result()
        except Exception:
            logger.exception("Async side effect dispatch failed")
