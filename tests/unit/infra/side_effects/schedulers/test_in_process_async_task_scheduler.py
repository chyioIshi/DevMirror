import asyncio
from collections.abc import Sequence
from dataclasses import dataclass, field

from app.domain.mocks.models import SideEffect, SideEffectContext, SideEffectType
from app.infra.side_effects.schedulers import InProcessAsyncTaskScheduler


@dataclass(slots=True)
class FakeSideEffectDispatcher:
    dispatch_calls: list[tuple[list[SideEffect], SideEffectContext]] = field(default_factory=list)

    async def dispatch(
        self,
        side_effects: Sequence[SideEffect],
        context: SideEffectContext,
    ) -> list[object]:
        self.dispatch_calls.append((list(side_effects), context))
        return []


class TestInProcessAsyncTaskScheduler:
    async def test_schedules_dispatch_in_current_event_loop(self) -> None:
        dispatcher = FakeSideEffectDispatcher()
        scheduler = InProcessAsyncTaskScheduler(dispatcher=dispatcher)
        side_effect = SideEffect(
            type=SideEffectType.MESSAGE_PUBLISH,
            provider="kafka",
            target={"topic": "events"},
            payload_template={"ok": True},
        )
        context = SideEffectContext(execution={"request_id": "request-1"})

        scheduler.schedule_side_effects([side_effect], context)

        while not dispatcher.dispatch_calls:
            await asyncio.sleep(0)

        assert dispatcher.dispatch_calls == [([side_effect], context)]
