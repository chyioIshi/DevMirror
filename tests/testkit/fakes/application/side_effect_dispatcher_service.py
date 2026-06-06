from collections.abc import Sequence
from dataclasses import dataclass, field

from app.domain.mocks.models import (
    SideEffect,
    SideEffectContext,
    SideEffectExecutionResult,
)


@dataclass(slots=True)
class FakeSideEffectDispatcherService:
    """Fake side effect dispatcher service used by application tests."""

    dispatch_calls: list[tuple[list[SideEffect], SideEffectContext]] = field(
        default_factory=list,
    )

    async def dispatch(
        self,
        side_effects: Sequence[SideEffect],
        context: SideEffectContext,
    ) -> list[SideEffectExecutionResult]:
        self.dispatch_calls.append((list(side_effects), context))
        return []
