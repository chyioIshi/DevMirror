import pytest

from app.application.mocks.use_cases.update_mock import update_mock


class TestUpdateMockPersistence:
    """Проверяет сохранение результата обновления мока."""

    @pytest.mark.asyncio
    async def test_saves_updated_mock(
        self,
        fake_mock_repository,
        mock_factory,
        command_factory,
    ) -> None:
        """Проверяет сохранение обновленного мока."""
        saved_mock = await fake_mock_repository.add(mock_factory.create_mock(name="old-name"))
        command = command_factory.update_mock(mock_id=saved_mock.id, name="new-name")

        await update_mock(command, fake_mock_repository)
        persisted_mock = await fake_mock_repository.get_by_id(saved_mock.id)

        assert persisted_mock is not None
        assert persisted_mock.name == "new-name"
