import pytest

from app.application.exceptions import (
    MockNotFoundError,
    OperationNotAllowedError,
    ValidationError,
)
from app.domain.mocks.models import MockListFilters
from tests.testkit.factories import CommandFactory


class TestCrud:
    """Проверяет CRUD-операции MockManagementService."""

    @pytest.mark.asyncio
    async def test_create_assigns_id(self, fake_mock_service, mock_factory) -> None:
        """Проверяет, что создание присваивает мокy идентификатор."""
        mock_model = mock_factory.create_mock()
        created_mock = await fake_mock_service.create_mock(mock_model)

        assert created_mock.id is not None

    @pytest.mark.asyncio
    async def test_create_sets_timestamps(self, fake_mock_service, mock_factory) -> None:
        """Проверяет, что создание заполняет timestamps."""
        mock_model = mock_factory.create_mock()
        created_mock = await fake_mock_service.create_mock(mock_model)

        assert created_mock.created_at is not None
        assert created_mock.updated_at is not None

    @pytest.mark.asyncio
    async def test_create_timestamps_are_equal_on_creation(
        self,
        fake_mock_service,
        mock_factory,
    ) -> None:
        """Проверяет, что created_at и updated_at равны при создании."""
        mock_model = mock_factory.create_mock()
        created_mock = await fake_mock_service.create_mock(mock_model)

        assert created_mock.created_at == created_mock.updated_at

    @pytest.mark.asyncio
    async def test_get_returns_created_mock(self, fake_mock_service, mock_factory) -> None:
        """Проверяет, что get возвращает ранее созданный мок."""
        mock_model = mock_factory.create_mock(name="my-mock")
        created_mock = await fake_mock_service.create_mock(mock_model)
        fetched_mock = await fake_mock_service.get_mock(created_mock.id)

        assert fetched_mock.id == created_mock.id
        assert fetched_mock.name == "my-mock"

    @pytest.mark.asyncio
    async def test_get_raises_not_found_for_unknown_id(self, fake_mock_service) -> None:
        """Проверяет, что get неизвестного id вызывает not found."""
        with pytest.raises(MockNotFoundError):
            await fake_mock_service.get_mock("000000000000000000000000")

    @pytest.mark.asyncio
    async def test_update_applies_patch(
        self,
        fake_mock_service,
        mock_factory,
        command_factory: CommandFactory,
    ) -> None:
        """Проверяет, что update применяет переданный patch."""
        mock_model = mock_factory.create_mock(name="old-name")
        created_mock = await fake_mock_service.create_mock(mock_model)
        updated_mock = await fake_mock_service.update_mock(
            command_factory.update_mock(mock_id=created_mock.id, name="new-name"),
        )

        assert updated_mock.name == "new-name"

    @pytest.mark.asyncio
    async def test_update_preserves_id_and_created_at(
        self,
        fake_mock_service,
        mock_factory,
        command_factory: CommandFactory,
    ) -> None:
        """Проверяет, что update сохраняет id и created_at."""
        mock_model = mock_factory.create_mock()
        created_mock = await fake_mock_service.create_mock(mock_model)
        updated_mock = await fake_mock_service.update_mock(
            command_factory.update_mock(mock_id=created_mock.id, name="changed"),
        )

        assert updated_mock.id == created_mock.id
        assert updated_mock.created_at == created_mock.created_at

    @pytest.mark.asyncio
    async def test_update_bumps_updated_at(
        self,
        fake_mock_service,
        mock_factory,
        command_factory: CommandFactory,
    ) -> None:
        """Проверяет, что update обновляет updated_at."""
        mock_model = mock_factory.create_mock()
        created_mock = await fake_mock_service.create_mock(mock_model)
        updated_mock = await fake_mock_service.update_mock(
            command_factory.update_mock(mock_id=created_mock.id, name="changed"),
        )

        assert updated_mock.updated_at >= created_mock.updated_at

    @pytest.mark.asyncio
    async def test_update_route_keeps_missing_method_or_path(
        self,
        fake_mock_service,
        mock_factory,
        command_factory: CommandFactory,
    ) -> None:
        """Проверяет, что update маршрута сохраняет отсутствующий method."""
        mock_model = mock_factory.create_mock(path="/before")
        created_mock = await fake_mock_service.create_mock(mock_model)
        updated_mock = await fake_mock_service.update_mock(
            command_factory.update_mock(mock_id=created_mock.id, path="/after"),
        )

        assert updated_mock.path == "/after"
        assert updated_mock.method == created_mock.method

    @pytest.mark.asyncio
    async def test_update_raises_not_found_for_unknown_id(
        self,
        fake_mock_service,
        command_factory: CommandFactory,
    ) -> None:
        """Проверяет, что update неизвестного id вызывает not found."""
        with pytest.raises(MockNotFoundError):
            await fake_mock_service.update_mock(
                command_factory.update_mock(mock_id="000000000000000000000000", name="x"),
            )

    @pytest.mark.asyncio
    async def test_delete_removes_mock(self, fake_mock_service, mock_factory) -> None:
        """Проверяет, что delete удаляет существующий мок."""
        mock_model = mock_factory.create_mock()
        created_mock = await fake_mock_service.create_mock(mock_model)

        await fake_mock_service.delete_mock(created_mock.id)

        with pytest.raises(MockNotFoundError):
            await fake_mock_service.get_mock(created_mock.id)

    @pytest.mark.asyncio
    async def test_delete_raises_not_found_for_unknown_id(self, fake_mock_service) -> None:
        """Проверяет, что delete неизвестного id вызывает not found."""
        with pytest.raises(MockNotFoundError):
            await fake_mock_service.delete_mock("000000000000000000000000")

    @pytest.mark.asyncio
    async def test_list_mocks_returns_all_created(self, fake_mock_service, mock_factory) -> None:
        """Проверяет, что list возвращает все созданные моки."""
        mock_model_a = mock_factory.create_mock(name="a", path="/a")
        mock_model_b = mock_factory.create_mock(name="b", path="/b")
        await fake_mock_service.create_mock(mock_model_a)
        await fake_mock_service.create_mock(mock_model_b)

        result = await fake_mock_service.list_mocks(MockListFilters())

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_list_mocks_respects_limit(self, fake_mock_service, mock_factory) -> None:
        """Проверяет, что list учитывает limit."""
        for index in range(5):
            await fake_mock_service.create_mock(
                mock_factory.create_mock(name=f"mock-{index}", path=f"/mock-{index}"),
            )

        result = await fake_mock_service.list_mocks(MockListFilters(), limit=2)

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_list_mocks_respects_offset(self, fake_mock_service, mock_factory) -> None:
        """Проверяет, что list учитывает offset."""
        for index in range(5):
            await fake_mock_service.create_mock(
                mock_factory.create_mock(name=f"mock-{index}", path=f"/mock-{index}"),
            )

        result = await fake_mock_service.list_mocks(MockListFilters(), limit=100, offset=3)

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_create_raises_operation_not_allowed_for_active_mock(
        self,
        fake_mock_service,
        mock_factory,
    ) -> None:
        """Проверяет, что создать активный мок напрямую нельзя."""
        mock_model = mock_factory.create_mock(active=True)
        with pytest.raises(OperationNotAllowedError):
            await fake_mock_service.create_mock(mock_model)

    @pytest.mark.asyncio
    async def test_update_raises_validation_error_for_empty_command(
        self,
        fake_mock_service,
        mock_factory,
        command_factory: CommandFactory,
    ) -> None:
        """Проверяет, что пустая команда update вызывает validation error."""
        mock_model = mock_factory.create_mock()
        created_mock = await fake_mock_service.create_mock(mock_model)
        update_mock_command = command_factory.update_mock(mock_id=created_mock.id)

        with pytest.raises(ValidationError):
            await fake_mock_service.update_mock(update_mock_command)
