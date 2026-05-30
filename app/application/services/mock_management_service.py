"""Application service for managing mock lifecycle operations."""

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
    """Coordinates creating, updating, activating, and deleting mocks."""

    def __init__(
        self,
        repository: MockRepository,
        conflict_service: MockConflictService,
        activation_policy: MockActivationPolicy,
    ) -> None:
        """Initializes the mock management service.

        Args:
            repository: Mock repository port.
            conflict_service: Domain service for detecting conflicting mocks.
            activation_policy: Policy that decides which conflicting mocks to deactivate.
        """
        self._repository = repository
        self._conflict_service = conflict_service
        self._activation_policy = activation_policy

    async def create_mock(self, mock: Mock) -> Mock:
        """Persists a new mock.

        Args:
            mock: Mock aggregate to persist.

        Returns:
            Persisted mock.

        Raises:
            OperationNotAllowedError: If the mock is already active before creation.
        """
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
            "Создан мок %s с id=%s, path=%s, method=%s",
            created_mock.name,
            created_mock.id,
            created_mock.path,
            created_mock.method,
            extra={
                "mock_id": created_mock.id,
                "mock_name": created_mock.name,
                "path": created_mock.path,
                "method": str(created_mock.method),
                "scope": created_mock.scope,
            },
        )
        return created_mock

    async def get_mock(self, mock_id: str) -> Mock:
        """Returns a mock by id or raises an error when it is not found.

        Args:
            mock_id: Mock identifier.

        Returns:
            Found mock.

        Raises:
            MockNotFoundError: If no mock exists with the given id.
        """
        mock = await self._repository.get_by_id(mock_id)
        if mock is None:
            raise MockNotFoundError(mock_id=mock_id)
        logger.debug("Получен мок с id=%s (get_mock)", mock_id, extra={"mock_id": mock_id})
        return mock

    async def list_mocks(
        self,
        filters: MockListFilters,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Mock]:
        """Returns mocks matching the provided filters.

        Args:
            filters: Filters applied to the mock list query.
            limit: Maximum number of mocks to return.
            offset: Number of mocks to skip.

        Returns:
            Matching mocks.
        """
        mocks = await self._repository.list_mocks(filters, limit=limit, offset=offset)
        logger.debug(
            f"Получено {len(mocks)} моков (list_mocks)",
            extra={"count": len(mocks), "limit": limit, "offset": offset},
        )
        return mocks

    async def update_mock(self, cmd: UpdateMockCommand) -> Mock:
        """Applies a partial update to an existing mock.

        Args:
            cmd: Update command containing the mock id and changed fields.

        Returns:
            Updated mock.

        Raises:
            MockNotFoundError: If no mock exists with the command id.
            ValidationError: If the command contains no changed fields.
        """
        updated_mock = await update_mock_use_case(cmd, self._repository)
        logger.info(
            "Обновлен мок %s с id=%s, path=%s, method=%s",
            updated_mock.name,
            updated_mock.id,
            updated_mock.path,
            updated_mock.method,
            extra={
                "mock_id": updated_mock.id,
                "path": updated_mock.path,
                "method": str(updated_mock.method),
                "scope": updated_mock.scope,
            },
        )
        return updated_mock

    async def delete_mock(self, mock_id: str) -> None:
        """Deletes a mock or raises an error when it is not found.

        Args:
            mock_id: Mock identifier.

        Raises:
            MockNotFoundError: If no mock exists with the given id.
        """
        await self.get_mock(mock_id)
        await self._repository.remove(mock_id)
        logger.info("Удален мок с id=%s (delete_mock)", mock_id, extra={"mock_id": mock_id})

    async def activate_mock(
        self,
        mock_id: str,
        *,
        deactivate_conflicting: bool = False,
    ) -> Mock:
        """Activates a mock and optionally deactivates conflicting mocks.

        Args:
            mock_id: Identifier of the mock to activate.
            deactivate_conflicting: Whether active conflicting mocks should be deactivated.

        Returns:
            Activated mock.

        Raises:
            MockNotFoundError: If no mock exists with the given id.
            OperationNotAllowedError: If the mock is already active.
            MockConflictError: If active conflicts exist and should not be deactivated.
        """
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
            "Активирован мок %s с id=%s, path=%s, method=%s",
            activated_mock.name,
            activated_mock.id,
            activated_mock.path,
            activated_mock.method,
            extra={
                "mock_id": activated_mock.id,
                "deactivated_conflicting_count": deactivated_conflicting_count,
            },
        )
        return activated_mock

    async def deactivate_mock(self, mock_id: str) -> Mock:
        """Deactivates the specified mock.

        Args:
            mock_id: Identifier of the mock to deactivate.

        Returns:
            Deactivated mock.

        Raises:
            MockNotFoundError: If no mock exists with the given id.
            OperationNotAllowedError: If the mock is already inactive.
        """
        current_mock = await self.get_mock(mock_id)
        if not current_mock.active:
            raise OperationNotAllowedError(
                "Mock is already inactive",
                details={"mock_id": current_mock.id},
            )
        current_mock.deactivate()
        deactivated_mock = await self._repository.save(current_mock)
        logger.info(
            "Деактивирован мок %s с id=%s",
            deactivated_mock.name,
            deactivated_mock.id,
            extra={"mock_id": deactivated_mock.id},
        )
        return deactivated_mock
