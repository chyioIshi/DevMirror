from datetime import UTC, datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field

from app.domain.mocks.models.match_rule import MatchRule
from app.domain.mocks.models.mock_response import MockResponse
from app.domain.mocks.models.mock_update import MockUpdate
from app.domain.shared.enums import HttpMethod


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
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))

    def conflicts_with(self, other: Self) -> bool:
        """Проверяет, конфликтует ли мок с другим (path + method + scope)."""
        return (
            self.path == other.path
            and self.method == other.method
            and self.scope == other.scope
            and self.match_rules == other.match_rules
            and self.id != other.id
        )

    def apply_update(self, update: MockUpdate) -> "Mock":
        """Применяет частичное обновление, возвращая новый экземпляр."""
        patch = update.to_patch_dict()
        patch["updated_at"] = datetime.now(tz=UTC)
        return self.model_copy(update=patch, deep=True)
