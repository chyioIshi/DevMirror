"""Response contract with request log verification result."""

from pydantic import BaseModel, ConfigDict, Field


class VerifyRequestLogResponse(BaseModel):
    """Response model with the request log verification result."""

    model_config = ConfigDict(extra="forbid")

    matched: bool = Field(examples=[True])
    actual_count: int = Field(examples=[1])
