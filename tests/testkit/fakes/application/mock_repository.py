from collections.abc import Iterable, Sequence
from dataclasses import replace

from app.domain.mocks.models import Mock, MockListFilters
from app.domain.shared import HttpMethod

type ListCandidatesCall = tuple[HttpMethod, str, tuple[str, ...]]


class FakeMockRepository:
    """In-memory fake MockRepository для application-тестов."""

    def __init__(self, mocks: Iterable[Mock] | None = None) -> None:
        self._store: dict[str, Mock] = {}
        self._counter = 0
        self.list_candidates_calls: list[ListCandidatesCall] = []

        for mock in mocks or ():
            saved = mock if mock.id is not None else replace(mock, id=self._next_id())
            self._store[saved.id] = saved

    async def add(self, mock: Mock) -> Mock:
        """Добавляет Mock и возвращает его с id."""
        saved = replace(mock, id=self._next_id())
        self._store[saved.id] = saved
        return saved

    async def get_by_id(self, mock_id: str) -> Mock | None:
        """Возвращает Mock по id."""
        return self._store.get(mock_id)

    async def save(self, mock: Mock) -> Mock:
        """Сохраняет Mock."""
        if mock.id is None:
            mock = replace(mock, id=self._next_id())
        self._store[mock.id] = mock
        return mock

    async def remove(self, mock_id: str) -> bool:
        """Удаляет Mock по id."""
        return self._store.pop(mock_id, None) is not None

    async def list_mocks(
        self,
        filters: MockListFilters,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Mock]:
        """Возвращает Mock с фильтрацией и пагинацией."""
        results = list(self._store.values())

        if filters.path is not None:
            results = [mock for mock in results if mock.path == filters.path]
        if filters.method is not None:
            results = [mock for mock in results if mock.method == filters.method]
        if filters.active is not None:
            results = [mock for mock in results if mock.active == filters.active]
        if filters.scope is not None:
            results = [mock for mock in results if mock.scope == filters.scope]

        return results[offset : offset + limit]

    async def list_candidates(
        self,
        method: HttpMethod,
        path: str,
        scopes: Sequence[str],
    ) -> list[Mock]:
        """Возвращает активных кандидатов для запроса."""
        self.list_candidates_calls.append((method, path, tuple(scopes)))
        return [
            mock
            for mock in self._store.values()
            if mock.active and mock.method == method and mock.path == path and mock.scope in scopes
        ]

    def persisted(self) -> list[Mock]:
        """Возвращает сохраненные Mock."""
        return list(self._store.values())

    def _next_id(self) -> str:
        self._counter += 1
        return f"{self._counter:024x}"
