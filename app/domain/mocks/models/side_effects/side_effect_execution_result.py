"""Side effect execution result model."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True, frozen=True)
class SideEffectExecutionResult:
    """Result returned by a side effect provider execution."""

    provider: str
    success: bool
    details: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def to_mapping(self) -> dict[str, Any]:
        """Return a broker-safe representation of this execution result."""
        return {
            "provider": self.provider,
            "success": self.success,
            "details": self.details,
            "error": self.error,
        }
