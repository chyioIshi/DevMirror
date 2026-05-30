"""Domain service for finding conflicts between mocks."""

from collections.abc import Sequence

from app.domain.mocks.models import Mock


class MockConflictService:
    """Finds conflicts among candidates when resolving a mock for a request."""

    def find_conflicts(self, target: Mock, candidates: Sequence[Mock]) -> list[Mock]:
        """Returns candidates that conflict with a target mock.

        Args:
            target: Mock for which conflicts are searched.
            candidates: Mock candidates to check.

        Returns:
            Mocks that conflict with `target`.
        """
        return [candidate for candidate in candidates if target.conflicts_with(candidate)]
