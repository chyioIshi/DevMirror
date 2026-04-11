
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field

from app.domain.models.enums import HttpMethod
from app.domain.models.mocks.match_rule import MatchRule
from app.domain.models.mocks.mock_response import MockResponse


class Mock(BaseModel):
    """Описывает полную структуру мока, хранимую сервисом."""

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    name: str
    description: str | None = None
    path: str
    method: HttpMethod
    priority: int = 0
    active: bool = True
    scope: str = "global"
    match_rules: list[MatchRule] = Field(default_factory=list)
    response: MockResponse
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
