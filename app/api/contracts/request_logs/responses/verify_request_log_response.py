
from pydantic import BaseModel, ConfigDict, Field


class VerifyRequestLogResponse(BaseModel):
    """Модель ответа с результатом проверки журнала."""

    model_config = ConfigDict(extra="forbid")

    matched: bool = Field(examples=[True])
    actual_count: int = Field(examples=[1])
