from app.application.commands import UpdateMockCommand
from app.domain.mocks.models import Mock, MockListFilters


class FakeMockManagementService:
    """Fake MockManagementService для integration-тестов API routes."""

    def __init__(
        self,
        *,
        created_mock: Mock,
        fetched_mock: Mock | None = None,
        listed_mocks: list[Mock] | None = None,
        updated_mock: Mock | None = None,
        activated_mock: Mock | None = None,
        deactivated_mock: Mock | None = None,
    ) -> None:
        self.created_mock = created_mock
        self.fetched_mock = fetched_mock or created_mock
        self.listed_mocks = listed_mocks or [created_mock]
        self.updated_mock = updated_mock or created_mock
        self.activated_mock = activated_mock or created_mock
        self.deactivated_mock = deactivated_mock or created_mock
        self.create_mock_calls: list[Mock] = []
        self.get_mock_calls: list[str] = []
        self.list_mocks_calls: list[tuple[MockListFilters, int, int]] = []
        self.update_mock_calls: list[UpdateMockCommand] = []
        self.delete_mock_calls: list[str] = []
        self.activate_mock_calls: list[tuple[str, bool]] = []
        self.deactivate_mock_calls: list[str] = []
        self.create_mock_error: Exception | None = None
        self.get_mock_error: Exception | None = None
        self.list_mocks_error: Exception | None = None
        self.update_mock_error: Exception | None = None
        self.delete_mock_error: Exception | None = None
        self.activate_mock_error: Exception | None = None
        self.deactivate_mock_error: Exception | None = None

    async def create_mock(self, mock: Mock) -> Mock:
        """Возвращает заранее заданный созданный мок."""
        self.create_mock_calls.append(mock)
        if self.create_mock_error is not None:
            raise self.create_mock_error
        return self.created_mock

    async def get_mock(self, mock_id: str) -> Mock:
        """Возвращает заранее заданный найденный мок."""
        self.get_mock_calls.append(mock_id)
        if self.get_mock_error is not None:
            raise self.get_mock_error
        return self.fetched_mock

    async def list_mocks(
        self,
        filters: MockListFilters,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Mock]:
        """Возвращает заранее заданный список моков."""
        self.list_mocks_calls.append((filters, limit, offset))
        if self.list_mocks_error is not None:
            raise self.list_mocks_error
        return self.listed_mocks

    async def update_mock(self, command: UpdateMockCommand) -> Mock:
        """Возвращает заранее заданный обновленный мок."""
        self.update_mock_calls.append(command)
        if self.update_mock_error is not None:
            raise self.update_mock_error
        return self.updated_mock

    async def delete_mock(self, mock_id: str) -> None:
        """Запоминает удаляемый mock id."""
        self.delete_mock_calls.append(mock_id)
        if self.delete_mock_error is not None:
            raise self.delete_mock_error

    async def activate_mock(
        self,
        mock_id: str,
        *,
        deactivate_conflicting: bool = False,
    ) -> Mock:
        """Возвращает заранее заданный активированный мок."""
        self.activate_mock_calls.append((mock_id, deactivate_conflicting))
        if self.activate_mock_error is not None:
            raise self.activate_mock_error
        return self.activated_mock

    async def deactivate_mock(self, mock_id: str) -> Mock:
        """Возвращает заранее заданный деактивированный мок."""
        self.deactivate_mock_calls.append(mock_id)
        if self.deactivate_mock_error is not None:
            raise self.deactivate_mock_error
        return self.deactivated_mock
