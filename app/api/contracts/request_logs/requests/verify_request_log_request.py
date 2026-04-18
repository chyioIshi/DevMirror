
from pydantic import BaseModel, ConfigDict, Field

from app.domain.shared.enums import HttpMethod


class VerifyRequestLogRequest(BaseModel):
    """Модель запроса для проверки наличия ожидаемого запроса в журнале."""

    model_config = ConfigDict(extra="forbid")

    path: str = Field(examples=["/hello"])
    method: HttpMethod = Field(examples=["GET"])
    expected_count: int | None = Field(default=None, examples=[1])
    matched_mock_id: str | None = Field(
        default=None,
        examples=["69d17fb0fa28a0c108a689eb"],
    )
