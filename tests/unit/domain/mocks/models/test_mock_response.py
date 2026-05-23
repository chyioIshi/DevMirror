import pytest

from app.domain.mocks import InvalidMockResponseError
from app.domain.mocks.models import MockResponse


class TestMockResponse:
    """Проверяет инварианты ответа мока."""

    @pytest.mark.parametrize("status_code", [100, 200, 599])
    def test_allows_valid_status_code(self, status_code: int) -> None:
        """Проверяет допустимые HTTP status code."""
        response = MockResponse(status_code=status_code)

        assert response.status_code == status_code

    @pytest.mark.parametrize("status_code", [99, 600])
    def test_rejects_invalid_status_code(self, status_code: int) -> None:
        """Проверяет запрет status code вне HTTP-диапазона."""
        with pytest.raises(InvalidMockResponseError):
            MockResponse(status_code=status_code)
