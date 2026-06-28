"""Queue routing for Celery side effect tasks."""

from collections.abc import Mapping, Sequence

from app.domain.mocks.models import SideEffect, SideEffectType


class CeleryQueueRouter:
    """Resolves Celery queue names for side effect execution."""

    def __init__(
        self,
        *,
        queues_by_type: Mapping[SideEffectType, str] | None = None,
        default_queue: str = "side_effects.default",
    ) -> None:
        self._queues_by_type = dict(queues_by_type or _DEFAULT_QUEUES_BY_TYPE)
        self._default_queue = default_queue

    def queue_for(self, side_effect: SideEffect) -> str:
        """Return the queue used for one side effect."""
        return self._queues_by_type.get(side_effect.type, self._default_queue)

    def queue_for_batch(self, side_effects: Sequence[SideEffect]) -> str:
        """Return the queue used for an ordered side effect batch."""
        queues = {self.queue_for(side_effect) for side_effect in side_effects}
        if len(queues) == 1:
            return next(iter(queues))

        return self._default_queue


_DEFAULT_QUEUES_BY_TYPE: dict[SideEffectType, str] = {
    SideEffectType.MESSAGE_PUBLISH: "side_effects.kafka",
    SideEffectType.HTTP_CALLBACK: "side_effects.http",
    SideEffectType.DB_INSERT: "side_effects.db",
    SideEffectType.DB_UPDATE: "side_effects.db",
}
