from collections.abc import Sequence

from app.domain.mocks.models.mock import Mock


class MockActivationPolicy:
    """Находит активные конфликтные моки при активации конкретного мока."""

    def resolve_conflicts(self, target: Mock, conflicts: Sequence[Mock]) -> list[Mock]:
        target_id = target.id
        return [
            conflict
            for conflict in conflicts
            if conflict.active and (target_id is None or conflict.id != target_id)
        ]
