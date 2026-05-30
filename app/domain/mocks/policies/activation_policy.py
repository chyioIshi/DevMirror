"""Conflict handling policy for mock activation."""

from collections.abc import Sequence

from app.domain.mocks.models import Mock


class MockActivationPolicy:
    """Finds active conflicting mocks when a target mock is activated."""

    def resolve_conflicts(self, target: Mock, conflicts: Sequence[Mock]) -> list[Mock]:
        """Returns active conflicts that should be deactivated.

        Args:
            target: Mock that is being activated.
            conflicts: Candidates that conflict with the target mock.

        Returns:
            Active conflicting mocks, excluding the target mock itself.
        """
        target_id = target.id
        return [
            conflict
            for conflict in conflicts
            if conflict.active and (target_id is None or conflict.id != target_id)
        ]
