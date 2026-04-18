
from datetime import UTC, datetime

from app.application.exceptions import MockNotFoundError
from app.domain.mocks.models import Mock, MockListFilters, MockUpdate
from app.domain.mocks.repository import MockRepository


class MockManagementService:
    """Управляет созданием, изменением, активацией и удалением моков."""

    def __init__(self, repo: MockRepository) -> None:
        """Инициализирует сервис с реализацией репозитория моков."""
        self._mock_repo = repo

    async def create_mock(self, mock: Mock) -> Mock:
        """Сохраняет новый мок."""
        now = datetime.now(tz=UTC)
        return await self._mock_repo.create(
            mock.model_copy(update={"created_at": now, "updated_at": now})
        )

    async def get_mock(self, mock_id: str) -> Mock:
        """Возвращает мок по id или вызывает исключение, если он не найден."""
        mock = await self._mock_repo.get_by_id(mock_id)
        if mock is None:
            raise MockNotFoundError(f"Mock `{mock_id}` was not found")
        return mock

    async def list_mocks(
        self, filters: MockListFilters, limit: int = 100, offset: int = 0,
    ) -> list[Mock]:
        """Возвращает список моков, подходящих под заданные фильтры."""
        return await self._mock_repo.list_mocks(filters, limit=limit, offset=offset)

    async def update_mock(self, mock_id: str, update: MockUpdate) -> Mock:
        """Применяет частичное обновление к существующему моку."""
        current_mock = await self.get_mock(mock_id)
        return await self._mock_repo.update(current_mock.apply_update(update))

    async def delete_mock(self, mock_id: str) -> None:
        """Удаляет мок или вызывает исключение, если он не найден."""
        await self.get_mock(mock_id)
        await self._mock_repo.delete(mock_id)

    async def activate_mock(
        self, mock_id: str, *, deactivate_conflicting: bool = False,
    ) -> Mock:
        """Активирует мок и при необходимости деактивирует конфликтующие."""
        current_mock = await self.get_mock(mock_id)

        if deactivate_conflicting:
            conflicts = await self._mock_repo.list_active_conflicts(current_mock)
            for conflict in conflicts:
                await self._mock_repo.update(
                    conflict.model_copy(
                        update={"active": False, "updated_at": datetime.now(tz=UTC)},
                    )
                )

        return await self._mock_repo.update(
            current_mock.model_copy(
                update={"active": True, "updated_at": datetime.now(tz=UTC)},
            )
        )

    async def deactivate_mock(self, mock_id: str) -> Mock:
        """Деактивирует указанный мок."""
        current_mock = await self.get_mock(mock_id)
        return await self._mock_repo.update(
            current_mock.model_copy(
                update={"active": False, "updated_at": datetime.now(tz=UTC)},
            )
        )
