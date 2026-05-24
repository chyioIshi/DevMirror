"""Политика обработки конфликтов при активации мока."""

from collections.abc import Sequence

from app.domain.mocks.models import Mock


class MockActivationPolicy:
    """Находит активные конфликтные моки при активации конкретного мока."""

    def resolve_conflicts(self, target: Mock, conflicts: Sequence[Mock]) -> list[Mock]:
        """Возвращает активные конфликты, которые нужно деактивировать.

        Args:
            target: Мок, который планируется активировать.
            conflicts: Кандидаты, конфликтующие с целевым моком.

        Returns:
            Список активных конфликтующих моков, исключая сам целевой мок.
        """
        target_id = target.id
        return [
            conflict
            for conflict in conflicts
            if conflict.active and (target_id is None or conflict.id != target_id)
        ]
