import pytest
from pydantic import ValidationError

from app.api.contracts.mocks import CreateMockRequest
from app.api.contracts.mocks.items import MockResponsePayloadItem
from app.domain.shared import HttpMethod


class TestCreateMockRequest:
    """Проверяет контракт запроса создания мока."""

    def test_rejects_active_field(self) -> None:
        """Проверяет запрет поля active в create request."""
        with pytest.raises(ValidationError):
            CreateMockRequest(
                name="test",
                path="/test",
                method=HttpMethod.GET,
                active=True,
                response=MockResponsePayloadItem(status_code=200),
            )
