import pytest

from app.application.exceptions import MockNotFoundError, ValidationError
from app.application.mocks.use_cases.update_mock import update_mock


class TestUpdateMockValidation:
    """Проверяет валидацию use case обновления мока."""

    @pytest.mark.asyncio
    async def test_raises_validation_error_for_empty_command(
        self,
        fake_mock_repository,
        command_factory,
    ) -> None:
        """Проверяет ошибку для команды без изменений."""
        command = command_factory.update_mock(mock_id="000000000000000000000001")

        with pytest.raises(ValidationError) as error:
            await update_mock(command, fake_mock_repository)

        assert error.value.details == {"mock_id": "000000000000000000000001"}

    @pytest.mark.asyncio
    async def test_raises_not_found_for_missing_mock(
        self,
        fake_mock_repository,
        command_factory,
    ) -> None:
        """Проверяет ошибку для отсутствующего мока."""
        command = command_factory.update_mock(
            mock_id="000000000000000000000001",
            name="new-name",
        )

        with pytest.raises(MockNotFoundError) as error:
            await update_mock(command, fake_mock_repository)

        assert error.value.details == {"mock_id": "000000000000000000000001"}
