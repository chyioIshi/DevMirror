import pytest
from pydantic import ValidationError

from app.api.contracts.mocks import UpdateMockRequest
from app.domain.shared import HttpMethod


class TestUpdateMockRequest:
    """Проверяет контракт запроса обновления мока."""

    def test_allows_empty_patch(self) -> None:
        """Проверяет создание пустого patch-запроса."""
        request = UpdateMockRequest()

        assert request.model_fields_set == set()

    def test_accepts_valid_path(self) -> None:
        """Проверяет корректный путь."""
        request = UpdateMockRequest(path="/updated", method=HttpMethod.POST)

        assert request.path == "/updated"
        assert request.method == HttpMethod.POST

    def test_rejects_path_without_slash(self) -> None:
        """Проверяет запрет пути без начального слеша."""
        with pytest.raises(ValidationError):
            UpdateMockRequest(path="updated")

    def test_rejects_extra_fields(self) -> None:
        """Проверяет запрет лишних полей."""
        with pytest.raises(ValidationError):
            UpdateMockRequest(unknown=True)

    def test_rejects_active_field(self) -> None:
        """Проверяет запрет поля active в update request."""
        with pytest.raises(ValidationError):
            UpdateMockRequest(active=True)
