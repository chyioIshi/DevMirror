from pydantic import BaseModel, ConfigDict

from app.domain.shared.enums import HttpMethod


class RequestLogVerificationExpectation(BaseModel):
    """Описывает ожидания для проверки журнала запросов."""

    model_config = ConfigDict(extra="forbid")

    path: str
    method: HttpMethod
    expected_count: int | None = None
    matched_mock_id: str | None = None
