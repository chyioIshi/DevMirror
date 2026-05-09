import logging

from app.application.commands import UpdateMockCommand
from app.application.exceptions import (
    MockNotFoundError,
    OperationNotAllowedError,
)
from app.application.use_cases import update_mock as update_mock_use_case
from app.domain.mocks import MockConflictError, MockRepository
from app.domain.mocks.models import Mock, MockListFilters
from app.domain.mocks.policies import MockActivationPolicy
from app.domain.mocks.services import MockConflictService

logger = logging.getLogger(__name__)


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

        created_mock = await self._repository.add(mock)
        logger.info(
            f"Создан мок {created_mock.name} с id={created_mock.id}, path={created_mock.path}, method={created_mock.method}",
            extra={
                "mock_id": created_mock.id,
                "name": created_mock.name,
                "path": created_mock.path,
                "method": str(created_mock.method),
                "scope": created_mock.scope,
            },
        )
        return created_mock

    async def get_mock(self, mock_id: str) -> Mock:
        """Возвращает мок по id или вызывает исключение, если он не найден."""
        mock = await self._repository.get_by_id(mock_id)
        if mock is None:
            raise MockNotFoundError(mock_id=mock_id)
        logger.debug(f"Получен мок с id={mock_id} (get_mock)", extra={"mock_id": mock_id})
        return mock

    async def list_mocks(
        self,
        filters: MockListFilters,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Mock]:
        """Возвращает список моков, подходящих под заданные фильтры."""
        mocks = await self._repository.list_mocks(filters, limit=limit, offset=offset)
        logger.debug(
            f"Получено {len(mocks)} моков (list_mocks)",
            extra={"count": len(mocks), "limit": limit, "offset": offset},
        )
        return mocks

    async def update_mock(self, cmd: UpdateMockCommand) -> Mock:
        """Применяет частичное обновление к существующему моку."""
        updated_mock = await update_mock_use_case(cmd, self._repository)
        logger.info(
            f"Обновлен мок {updated_mock.name} с id={updated_mock.id}, path={updated_mock.path}, method={updated_mock.method}",
            extra={
                "mock_id": updated_mock.id,
                "path": updated_mock.path,
                "method": str(updated_mock.method),
                "scope": updated_mock.scope,
            },
        )
        return updated_mock

    async def delete_mock(self, mock_id: str) -> None:
        """Удаляет мок или вызывает исключение, если он не найден."""
        await self.get_mock(mock_id)
        await self._repository.remove(mock_id)
        logger.info(f"Удален мок с id={mock_id} (delete_mock)", extra={"mock_id": mock_id})

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

        deactivated_conflicting_count = 0
        if deactivate_conflicting:
            mocks_to_deactivate = self._activation_policy.resolve_conflicts(
                target=current_mock,
                conflicts=conflicts,
            )
            deactivated_conflicting_count = len(mocks_to_deactivate)

            for conflict in mocks_to_deactivate:
                conflict.deactivate()

            current_mock.activate()

            for conflict in mocks_to_deactivate:
                await self._repository.save(conflict)
        else:
            current_mock.activate()

        activated_mock = await self._repository.save(current_mock)
        logger.info(
            f"Активирован мок {activated_mock.name} с id={activated_mock.id}, path={activated_mock.path}, method={activated_mock.method}",
            extra={
                "mock_id": activated_mock.id,
                "deactivated_conflicting_count": deactivated_conflicting_count,
            },
        )
        return activated_mock

    async def deactivate_mock(self, mock_id: str) -> Mock:
        """Деактивирует указанный мок."""
        current_mock = await self.get_mock(mock_id)
        if not current_mock.active:
            raise OperationNotAllowedError(
                "Mock is already inactive",
                details={"mock_id": current_mock.id},
            )
        current_mock.deactivate()
        deactivated_mock = await self._repository.save(current_mock)
        logger.info(f"Деактивирован мок {deactivated_mock.name} с id={deactivated_mock.id}", extra={"mock_id": deactivated_mock.id})
        return deactivated_mock
