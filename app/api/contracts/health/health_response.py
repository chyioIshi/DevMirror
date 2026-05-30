"""Healthcheck response contract."""

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    """Response model for service health checks."""

    model_config = ConfigDict(extra="forbid")

    status: str = Field(examples=["ok"])
