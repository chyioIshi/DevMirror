from typing import Any

from pydantic import BaseModel, ConfigDict

from app.domain.shared.enums import HttpMethod


class MatchedMock(BaseModel):
    """Описывает найденный мок для запроса в журнале."""
    model_config = ConfigDict(extra="forbid")
    id: str
    name: str
    path: str
    method: HttpMethod
    scope: str
    response_status_code: int
    response_body: Any | None = None
