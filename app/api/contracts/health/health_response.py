
from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    """Модель ответа для проверки здоровья сервиса."""

    model_config = ConfigDict(extra="forbid")

    status: str = Field(examples=["ok"])
