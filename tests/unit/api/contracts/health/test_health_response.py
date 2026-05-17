import pytest
from pydantic import ValidationError

from app.api.contracts.health import HealthResponse


class TestHealthResponse:
    """Проверяет контракт health response."""

    def test_accepts_status(self) -> None:
        """Проверяет создание ответа со статусом."""
        response = HealthResponse(status="ok")

        assert response.status == "ok"

    def test_rejects_extra_fields(self) -> None:
        """Проверяет запрет лишних полей."""
        with pytest.raises(ValidationError):
            HealthResponse(status="ok", details={})

