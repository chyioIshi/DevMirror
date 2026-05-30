"""Expectation model for request log verification."""

from dataclasses import dataclass

from app.domain.shared import HttpMethod


@dataclass(slots=True, frozen=True)
class RequestLogVerificationExpectation:
    """Describes an expectation for request log verification."""

    path: str
    method: HttpMethod
    expected_count: int | None = None
    matched_mock_id: str | None = None
