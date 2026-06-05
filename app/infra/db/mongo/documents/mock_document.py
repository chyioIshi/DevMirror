"""MongoDB documents used to persist mock definitions."""

from datetime import UTC, datetime
from typing import Any

from beanie import Document
from pydantic import BaseModel, Field
from pymongo import ASCENDING, DESCENDING

from app.domain.mocks.models import SideEffectFailPolicy, SideEffectMode, SideEffectType
from app.domain.shared import HttpMethod, MatchOperator, MatchSource


class MatchRuleDocument(BaseModel):
    """Nested Mongo document describing one request matching rule."""

    source: MatchSource
    key: str = ""
    operator: MatchOperator
    expected: Any | None = None


class SideEffectDocument(BaseModel):
    """Nested Mongo document describing a declared side effect."""

    type: SideEffectType
    provider: str
    target: dict[str, Any]
    payload_template: dict[str, Any]
    options: dict[str, Any] = Field(default_factory=dict)
    mode: SideEffectMode = SideEffectMode.ASYNC
    fail_policy: SideEffectFailPolicy = SideEffectFailPolicy.IGNORE
    enabled: bool = True


class MockResponseDocument(BaseModel):
    """Nested Mongo document describing a mock HTTP response."""

    status_code: int
    headers: dict[str, str] = Field(default_factory=dict)
    body: Any | None = None
    side_effects: list[SideEffectDocument] = Field(default_factory=list)


class MockDocument(Document):
    """Mongo document used to persist configured mocks."""

    name: str
    description: str | None = None
    path: str
    method: HttpMethod
    priority: int = 0
    active: bool = False
    scope: str = "global"
    match_rules: list[MatchRuleDocument] = Field(default_factory=list)
    response: MockResponseDocument
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))

    class Settings:
        """Beanie collection settings for mocks."""

        name: str = "mocks"
        indexes: list[list[tuple[str, int]]] = [
            [
                ("path", ASCENDING),
                ("method", ASCENDING),
                ("scope", ASCENDING),
                ("active", ASCENDING),
            ],
            [("active", ASCENDING), ("updated_at", DESCENDING)],
            [("tags", ASCENDING)],
        ]
