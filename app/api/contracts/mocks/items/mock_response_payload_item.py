from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MockResponsePayloadItem(BaseModel):
    """Вложенная DTO-модель ответа, описанного в моке."""

    model_config = ConfigDict(extra="forbid")

    status_code: int = Field(ge=100, le=599, examples=[200])
    headers: dict[str, str] = Field(
        default_factory=dict,
        examples=[{"Content-Type": "application/json"}],
    )
    body: Any | None = Field(
        default=None,
        examples=[{"message": "hello from mock"}],
    )
