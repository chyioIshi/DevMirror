"""Request log verification result model."""

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class RequestLogVerificationResult:
    """Stores the request log verification result."""

    matched: bool
    actual_count: int
