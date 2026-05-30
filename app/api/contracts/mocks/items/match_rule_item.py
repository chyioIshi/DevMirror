"""Request matching rule contract for mock APIs."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domain.shared import MatchOperator, MatchSource


class MatchRuleItem(BaseModel):
    """Nested DTO model for a mock matching rule."""

    model_config = ConfigDict(extra="forbid")

    source: MatchSource = Field(examples=["header"])
    key: str = Field(default="", examples=["x-test-user"])
    operator: MatchOperator = Field(examples=["eq"])
    expected: Any | None = Field(default=None, examples=["user123"])
