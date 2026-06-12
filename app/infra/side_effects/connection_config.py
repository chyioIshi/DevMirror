"""Side effect provider connection configuration."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ConnectionConfig(BaseModel):
    """Configuration for a named side effect provider connection."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    settings: dict[str, Any] = Field(default_factory=dict)
