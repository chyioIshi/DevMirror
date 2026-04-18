
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MockResponse(BaseModel):
    """Описывает HTTP-ответ, который должен вернуть сохранённый мок."""
    model_config = ConfigDict(extra="forbid")

    status_code: int = Field(ge=100, le=599)
    headers: dict[str, str] = Field(default_factory=dict)
    body: Any | None = None
