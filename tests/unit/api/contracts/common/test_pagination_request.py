import pytest
from pydantic import ValidationError

from app.api.contracts.common import PaginationRequest


class TestPaginationRequest:
    """Проверяет контракт пагинации."""

    def test_uses_default_values(self) -> None:
        """Проверяет значения пагинации по умолчанию."""
        request = PaginationRequest()

        assert request.limit == 100
        assert request.offset == 0

    def test_rejects_invalid_limit(self) -> None:
        """Проверяет запрет некорректного limit."""
        with pytest.raises(ValidationError):
            PaginationRequest(limit=0)

    def test_rejects_invalid_offset(self) -> None:
        """Проверяет запрет некорректного offset."""
        with pytest.raises(ValidationError):
            PaginationRequest(offset=-1)

    def test_rejects_extra_fields(self) -> None:
        """Проверяет запрет лишних полей."""
        with pytest.raises(ValidationError):
            PaginationRequest(limit=10, unknown=True)

