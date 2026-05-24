"""Доменный сервис поиска конфликтов между моками."""

from collections.abc import Sequence

from app.domain.mocks.models import Mock


class MockConflictService:
    """Находит конфликты среди кандидатов при резолвинге мока на запрос."""

    def find_conflicts(self, target: Mock, candidates: Sequence[Mock]) -> list[Mock]:
        """Возвращает кандидатов, конфликтующих с целевым моком.

        Args:
            target: Мок, для которого выполняется поиск конфликтов.
            candidates: Моки-кандидаты для проверки.

        Returns:
            Список моков, конфликтующих с `target`.
        """
        return [candidate for candidate in candidates if target.conflicts_with(candidate)]
