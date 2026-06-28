"""Mock HTTP response contract for API requests and responses."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.api.contracts.mocks.items.side_effect_item import SideEffectItem


class MockResponsePayloadItem(BaseModel):
    """Nested DTO model for the response described by a mock."""

    model_config = ConfigDict(extra="forbid")

    status_code: int = Field(ge=100, le=599, examples=[200])
    headers: dict[str, str] = Field(
        default_factory=dict,
        examples=[{"Content-Type": "application/json"}],
    )
    body: Any | None = Field(
        default=None,
        examples=[{"message": "hello from mock"}],
    )
    side_effects: list[SideEffectItem] = Field(default_factory=list)
