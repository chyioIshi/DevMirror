from collections.abc import Sequence

from app.domain.mocks.models.mock import Mock


class MockConflictService:
    """Находит конфликты среди кандидатов при резолвинге мока на запрос."""

    def find_conflicts(self, target: Mock, candidates: Sequence[Mock]) -> list[Mock]:
        return [
            candidate
            for candidate in candidates
            if target.conflicts_with(candidate)
        ]
