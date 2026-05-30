"""Shared pagination request contract for list API endpoints."""

from pydantic import BaseModel, ConfigDict, Field


class PaginationRequest(BaseModel):
    """Optional pagination parameters for entity list requests."""

    model_config = ConfigDict(extra="forbid")

    limit: int = Field(default=100, ge=1, le=1000, examples=[100])
    offset: int = Field(default=0, ge=0, examples=[0])
