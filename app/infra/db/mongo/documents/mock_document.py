
from datetime import UTC, datetime
from typing import Any

from beanie import Document
from pydantic import BaseModel, Field
from pymongo import ASCENDING, DESCENDING

from app.domain.shared.enums import HttpMethod, MatchOperator, MatchSource


class MatchRuleDocument(BaseModel):
    """Вложенный Mongo-документ, описывающий одно правило сопоставления запроса."""
    source: MatchSource
    key: str = ""
    operator: MatchOperator
    expected: Any | None = None


class MockResponseDocument(BaseModel):
    """Вложенный Mongo-документ, описывающий подставляемый HTTP-ответ."""
    status_code: int
    headers: dict[str, str] = Field(default_factory=dict)
    body: Any | None = None


class MockDocument(Document):
    """Основной Mongo-документ для хранения определений моков."""
    name: str
    description: str | None = None
    path: str
    method: HttpMethod
    priority: int = 0
    active: bool = True
    scope: str = "global"
    match_rules: list[MatchRuleDocument] = Field(default_factory=list)
    response: MockResponseDocument
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))

    class Settings:
        """Настройки коллекции Beanie и индексы для моков."""
        name: str = "mocks"
        indexes: list[list[tuple[str, int]]] = [
            [("path", ASCENDING), ("method", ASCENDING), ("scope", ASCENDING), ("active", ASCENDING)],
            [("active", ASCENDING), ("updated_at", DESCENDING)],
            [("tags", ASCENDING)],
        ]
