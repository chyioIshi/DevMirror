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
