"""Mock response side effect contract for API requests and responses."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domain.mocks.models import SideEffectFailPolicy, SideEffectMode, SideEffectType


class SideEffectItem(BaseModel):
    """Nested DTO model for a mock response side effect declaration."""

    model_config = ConfigDict(extra="forbid")

    type: SideEffectType = Field(examples=["message_publish"])
    provider: str = Field(min_length=1, examples=["kafka"])
    target: dict[str, Any] = Field(examples=[{"topic": "user-events"}])
    payload_template: dict[str, Any] = Field(examples=[{"user_id": "{{body.id}}"}])
    options: dict[str, Any] = Field(default_factory=dict)
    mode: SideEffectMode = Field(default=SideEffectMode.ASYNC, examples=["async"])
    fail_policy: SideEffectFailPolicy = Field(
        default=SideEffectFailPolicy.IGNORE,
        examples=["ignore"],
    )
    enabled: bool = Field(default=True)
