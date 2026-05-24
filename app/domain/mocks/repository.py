"""Порт репозитория моков."""

from collections.abc import Sequence
from typing import Protocol

from app.domain.mocks.models.mock import Mock
from app.domain.mocks.models.mock_list_filters import MockListFilters
from app.domain.shared import HttpMethod


class MockRepository(Protocol):
    """Описывает операции хранения и получения моков."""

    async def add(self, mock: Mock) -> Mock:
        """Сохраняет новое определение мока."""
        ...

    async def get_by_id(self, mock_id: str) -> Mock | None:
        """Возвращает мок по идентификатору или ``None``, если он не найден."""
        ...

    async def save(self, mock: Mock) -> Mock:
        """Сохраняет изменения существующего мока."""
        ...

    async def remove(self, mock_id: str) -> bool:
        """Удаляет мок и сообщает, успешно ли выполнена операция."""
        ...

    async def list_mocks(
        self,
        filters: MockListFilters,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Mock]:
        """Возвращает список моков с поддержкой пагинации."""
        ...

    async def list_candidates(
        self,
        method: HttpMethod,
        path: str,
        scopes: Sequence[str],
    ) -> list[Mock]:
        """Возвращает моки, которые можно рассматривать при резолвинге."""
        ...
