import pytest

from app.application.exceptions import OperationNotAllowedError
from app.application.services import MockManagementService
from app.domain.mocks import MockConflictError
from app.domain.mocks.models import Mock
from app.domain.shared import MatchOperator, MatchSource


class TestActivation:
    """Проверяет активацию и деактивацию моков."""

    @pytest.mark.asyncio
    async def test_activate_sets_active_true(
        self,
        fake_mock_service: MockManagementService,
        mock_factory,
    ) -> None:
        """Проверяет, что активация переводит мок в active=True."""
        mock_model: Mock = mock_factory.create_mock(active=False)
        created_mock: Mock = await fake_mock_service.create_mock(mock_model)
        activated_mock: Mock = await fake_mock_service.activate_mock(created_mock.id)

        assert activated_mock.active is True

    @pytest.mark.asyncio
    async def test_activate_bumps_updated_at(
        self,
        fake_mock_service: MockManagementService,
        mock_factory,
    ) -> None:
        """Проверяет, что активация обновляет updated_at."""
        mock_model: Mock = mock_factory.create_mock(active=False)
        created_mock: Mock = await fake_mock_service.create_mock(mock_model)
        activated_mock: Mock = await fake_mock_service.activate_mock(created_mock.id)

        assert activated_mock.updated_at >= created_mock.updated_at

    @pytest.mark.asyncio
    async def test_deactivate_sets_active_false(
        self,
        fake_mock_service: MockManagementService,
        mock_factory,
    ) -> None:
        """Проверяет, что деактивация переводит мок в active=False."""
        mock_model: Mock = mock_factory.create_mock(active=False)
        created_mock: Mock = await fake_mock_service.create_mock(mock_model)
        activated_mock: Mock = await fake_mock_service.activate_mock(created_mock.id)
        deactivated_mock: Mock = await fake_mock_service.deactivate_mock(activated_mock.id)

        assert deactivated_mock.active is False

    @pytest.mark.asyncio
    async def test_deactivate_bumps_updated_at(
        self,
        fake_mock_service: MockManagementService,
        mock_factory,
    ) -> None:
        """Проверяет, что деактивация обновляет updated_at."""
        mock_model: Mock = mock_factory.create_mock()
        created_mock: Mock = await fake_mock_service.create_mock(mock_model)
        activated_mock: Mock = await fake_mock_service.activate_mock(created_mock.id)
        deactivated_mock: Mock = await fake_mock_service.deactivate_mock(activated_mock.id)

        assert deactivated_mock.updated_at >= activated_mock.updated_at

    @pytest.mark.asyncio
    async def test_activate_with_deactivate_conflicting_disables_conflicts(
        self,
        fake_mock_service: MockManagementService,
        mock_factory,
    ) -> None:
        """Проверяет, что активация с флагом деактивирует конфликты."""
        conflict_mock_model: Mock = mock_factory.create_mock()
        target_mock_model: Mock = mock_factory.create_mock()

        conflict_mock: Mock = await fake_mock_service.create_mock(conflict_mock_model)
        await fake_mock_service.activate_mock(conflict_mock.id)
        target_mock: Mock = await fake_mock_service.create_mock(target_mock_model)

        await fake_mock_service.activate_mock(target_mock.id, deactivate_conflicting=True)

        conflict_mock = await fake_mock_service.get_mock(conflict_mock.id)
        assert conflict_mock.active is False

    @pytest.mark.asyncio
    async def test_activate_without_flag_raises_conflict(
        self,
        fake_mock_service: MockManagementService,
        mock_factory,
    ) -> None:
        """Проверяет, что конфликт без флага вызывает ошибку."""
        conflict_mock_model: Mock = mock_factory.create_mock()
        target_mock_model: Mock = mock_factory.create_mock()

        conflict_mock: Mock = await fake_mock_service.create_mock(conflict_mock_model)
        await fake_mock_service.activate_mock(conflict_mock.id)
        target = await fake_mock_service.create_mock(target_mock_model)

        with pytest.raises(MockConflictError):
            await fake_mock_service.activate_mock(target.id, deactivate_conflicting=False)

        refreshed_conflict = await fake_mock_service.get_mock(conflict_mock.id)
        assert refreshed_conflict.active is True

    @pytest.mark.asyncio
    async def test_activate_does_not_disable_coarse_non_conflicts(
        self,
        fake_mock_service: MockManagementService,
        mock_factory,
    ) -> None:
        """Проверяет, что грубые не-конфликты остаются активными."""
        mock_candidate = await fake_mock_service.create_mock(
            mock_factory.create_mock(
                match_rules=[
                    mock_factory.match_rule(
                        source=MatchSource.QUERY,
                        key="variant",
                        operator=MatchOperator.EQ,
                        expected="a",
                    ),
                ],
            ),
        )
        activated_mock_candidate = await fake_mock_service.activate_mock(mock_candidate.id)
        target_mock = await fake_mock_service.create_mock(mock_factory.create_mock())

        await fake_mock_service.activate_mock(target_mock.id, deactivate_conflicting=True)

        mock_candidate = await fake_mock_service.get_mock(activated_mock_candidate.id)
        assert mock_candidate.active is True

    @pytest.mark.asyncio
    async def test_activate_already_active_mock_raises_operation_not_allowed(
        self,
        fake_mock_service: MockManagementService,
        mock_factory,
    ) -> None:
        """Проверяет, что повторная активация активного мока запрещена."""
        mock_model: Mock = mock_factory.create_mock()
        created_mock = await fake_mock_service.create_mock(mock_model)
        activated_created_mock = await fake_mock_service.activate_mock(created_mock.id)

        with pytest.raises(OperationNotAllowedError):
            await fake_mock_service.activate_mock(activated_created_mock.id)

    @pytest.mark.asyncio
    async def test_deactivate_already_inactive_mock_raises_operation_not_allowed(
        self,
        fake_mock_service: MockManagementService,
        mock_factory,
    ) -> None:
        """Проверяет, что деактивация неактивного мока запрещена."""
        mock_model: Mock = mock_factory.create_mock()
        activated_created_mock = await fake_mock_service.create_mock(mock_model)

        with pytest.raises(OperationNotAllowedError):
            await fake_mock_service.deactivate_mock(activated_created_mock.id)
