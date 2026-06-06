from collections.abc import Coroutine
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class FakeAsyncTaskScheduler:
    """Fake async task scheduler used by application tests."""

    scheduled: list[Coroutine[Any, Any, None]] = field(default_factory=list)

    def schedule(self, coroutine: Coroutine[Any, Any, None]) -> None:
        self.scheduled.append(coroutine)
