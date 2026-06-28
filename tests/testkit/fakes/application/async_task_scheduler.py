from collections.abc import Sequence
from dataclasses import dataclass, field

from app.domain.mocks.models import SideEffect, SideEffectContext


@dataclass(slots=True)
class ScheduledSideEffects:
    side_effects: list[SideEffect]
    context: SideEffectContext


@dataclass(slots=True)
class FakeAsyncTaskScheduler:
    """Fake async task scheduler used by application tests."""

    scheduled: list[ScheduledSideEffects] = field(default_factory=list)

    def schedule_side_effects(
        self,
        side_effects: Sequence[SideEffect],
        context: SideEffectContext,
    ) -> None:
        self.scheduled.append(
            ScheduledSideEffects(
                side_effects=list(side_effects),
                context=context,
            )
        )
