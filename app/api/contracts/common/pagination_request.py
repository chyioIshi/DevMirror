
from pydantic import BaseModel, ConfigDict, Field


class PaginationRequest(BaseModel):
    """Опциональные параметры пагинации для запросов на список сущностей."""

    model_config = ConfigDict(extra="forbid")

    limit: int = Field(default=100, ge=1, le=1000, examples=[100])
    offset: int = Field(default=0, ge=0, examples=[0])
