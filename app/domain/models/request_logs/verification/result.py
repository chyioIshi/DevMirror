
from pydantic import BaseModel, ConfigDict


class RequestLogVerificationResult(BaseModel):
    """Хранит результат проверки журнала запросов."""

    model_config = ConfigDict(extra="forbid")

    matched: bool
    actual_count: int
