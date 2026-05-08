from app.application.commands.update_mock_command import UpdateMockCommand
from app.application.exceptions import (
    MockNotFoundError,
    OperationNotAllowedError,
)
from app.application.use_cases.update_mock import update_mock as update_mock_use_case
from app.domain.mocks.exceptions import MockConflictError
from app.domain.mocks.models import Mock, MockListFilters
from app.domain.mocks.policies.activation_policy import MockActivationPolicy
from app.domain.mocks.repository import MockRepository
from app.domain.mocks.services.conflict_service import MockConflictService


class MockManagementService:
    """Управляет созданием, изменением, активацией и удалением моков."""

    def __init__(
        self,
        repository: MockRepository,
        conflict_service: MockConflictService,
        activation_policy: MockActivationPolicy,
    ) -> None:
        self._repository = repository
        self._conflict_service = conflict_service
        self._activation_policy = activation_policy

    async def create_mock(self, mock: Mock) -> Mock:
        """Сохраняет новый мок."""
        if mock.active:
            raise OperationNotAllowedError(
                "Active mocks cannot be created directly",
                details={
                    "path": mock.path,
                    "method": str(mock.method),
                    "scope": mock.scope,
                },
            )

        return await self._repository.add(mock)

    async def get_mock(self, mock_id: str) -> Mock:
        """Возвращает мок по id или вызывает исключение, если он не найден."""
        mock = await self._repository.get_by_id(mock_id)
        if mock is None:
            raise MockNotFoundError(mock_id=mock_id)
        return mock

    async def list_mocks(
        self,
        filters: MockListFilters,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Mock]:
        """Возвращает список моков, подходящих под заданные фильтры."""
        return await self._repository.list_mocks(filters, limit=limit, offset=offset)

    async def update_mock(self, cmd: UpdateMockCommand) -> Mock:
        """Применяет частичное обновление к существующему моку."""
        return await update_mock_use_case(cmd, self._repository)

    async def delete_mock(self, mock_id: str) -> None:
        """Удаляет мок или вызывает исключение, если он не найден."""
        await self.get_mock(mock_id)
        await self._repository.remove(mock_id)

    async def activate_mock(
        self,
        mock_id: str,
        *,
        deactivate_conflicting: bool = False,
    ) -> Mock:
        """Активирует мок и при необходимости деактивирует конфликтующие."""
        current_mock = await self.get_mock(mock_id)

        if current_mock.active:
            raise OperationNotAllowedError(
                "Mock is already active",
                details={"mock_id": current_mock.id},
            )

        candidates = await self._repository.list_candidates(
            method=current_mock.method,
            path=current_mock.path,
            scopes=[current_mock.scope],
        )
        conflicts = self._conflict_service.find_conflicts(
            target=current_mock,
            candidates=candidates,
        )

        if conflicts and not deactivate_conflicting:
            raise MockConflictError(
                "Mock conflicts with active mocks",
                details={
                    "mock_id": current_mock.id,
                    "conflicting_mock_ids": [conflict.id for conflict in conflicts],
                },
            )

        if deactivate_conflicting:
            mocks_to_deactivate = self._activation_policy.resolve_conflicts(
                target=current_mock,
                conflicts=conflicts,
            )

            for conflict in mocks_to_deactivate:
                conflict.deactivate()

            current_mock.activate()

            for conflict in mocks_to_deactivate:
                await self._repository.save(conflict)
        else:
            current_mock.activate()

        return await self._repository.save(current_mock)

    async def deactivate_mock(self, mock_id: str) -> Mock:
        """Деактивирует указанный мок."""
        current_mock = await self.get_mock(mock_id)
        if not current_mock.active:
            raise OperationNotAllowedError(
                "Mock is already inactive",
                details={"mock_id": current_mock.id},
            )
        current_mock.deactivate()
        return await self._repository.save(current_mock)
