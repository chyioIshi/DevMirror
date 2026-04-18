from pydantic import BaseModel, ConfigDict

from app.domain.shared.enums import HttpMethod


class MockListFilters(BaseModel):
    """Описывает необязательные фильтры для получения списка моков."""
    model_config = ConfigDict(extra="forbid")

    path: str | None = None
    method: HttpMethod | None = None
    active: bool | None = None
    scope: str | None = None