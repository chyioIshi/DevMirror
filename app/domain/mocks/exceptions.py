"""Domain exceptions and error codes for mocks."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class DomainErrorCode(StrEnum):
    """Error codes for the mock domain layer."""

    MOCK_INVARIANT_ERROR = "MOCK_INVARIANT_ERROR"
    INVALID_MOCK_ROUTE = "INVALID_MOCK_ROUTE"
    INVALID_MOCK_STATE = "INVALID_MOCK_STATE"
    INVALID_MATCH_RULE = "INVALID_MATCH_RULE"
    INVALID_MOCK_RESPONSE = "INVALID_MOCK_RESPONSE"
    INVALID_SIDE_EFFECT = "INVALID_SIDE_EFFECT"
    INVALID_SCOPE = "INVALID_SCOPE"
    MOCK_CONFLICT = "MOCK_CONFLICT"


@dataclass(eq=False)
class DomainError(Exception):
    """Base domain error."""

    code: DomainErrorCode
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initializes the base `Exception` with the domain error message."""
        Exception.__init__(self, self.message)


class MockInvariantError(DomainError):
    """Error raised when a `Mock` aggregate invariant is violated."""

    def __init__(
        self,
        message: str = "Mock invariant was violated",
        details: dict[str, Any] | None = None,
        *,
        code: DomainErrorCode = DomainErrorCode.MOCK_INVARIANT_ERROR,
    ) -> None:
        """Creates a mock invariant violation error.

        Args:
            message: Readable error description.
            details: Additional error details.
            code: Domain error code.
        """
        super().__init__(code=code, message=message, details=details or {})


class InvalidMockRouteError(MockInvariantError):
    """Error raised when a mock route is invalid."""

    def __init__(
        self,
        message: str = "Mock route is invalid",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Creates an invalid mock route error.

        Args:
            message: Readable error description.
            details: Additional error details.
        """
        super().__init__(
            message=message,
            details=details,
            code=DomainErrorCode.INVALID_MOCK_ROUTE,
        )


class InvalidMockStateError(MockInvariantError):
    """Error raised when a mock state is invalid."""

    def __init__(
        self,
        message: str = "Mock state is invalid",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Creates an invalid mock state error.

        Args:
            message: Readable error description.
            details: Additional error details.
        """
        super().__init__(
            message=message,
            details=details,
            code=DomainErrorCode.INVALID_MOCK_STATE,
        )


class InvalidMatchRuleError(MockInvariantError):
    """Error raised when a request matching rule is invalid."""

    def __init__(
        self,
        message: str = "Match rule is invalid",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Creates an invalid match rule error.

        Args:
            message: Readable error description.
            details: Additional error details.
        """
        super().__init__(
            message=message,
            details=details,
            code=DomainErrorCode.INVALID_MATCH_RULE,
        )


class InvalidMockResponseError(MockInvariantError):
    """Error raised when a mock response is invalid."""

    def __init__(
        self,
        message: str = "Mock response is invalid",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Creates an invalid mock response error.

        Args:
            message: Readable error description.
            details: Additional error details.
        """
        super().__init__(
            message=message,
            details=details,
            code=DomainErrorCode.INVALID_MOCK_RESPONSE,
        )


class InvalidSideEffectError(MockInvariantError):
    """Error raised when a mock response side effect is invalid."""

    def __init__(
        self,
        message: str = "Side effect is invalid",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Creates an invalid side effect error.

        Args:
            message: Readable error description.
            details: Additional error details.
        """
        super().__init__(
            message=message,
            details=details,
            code=DomainErrorCode.INVALID_SIDE_EFFECT,
        )


class InvalidScopeError(MockInvariantError):
    """Error raised when a mock scope is invalid."""

    def __init__(
        self,
        message: str = "Mock scope is invalid",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Creates an invalid mock scope error.

        Args:
            message: Readable error description.
            details: Additional error details.
        """
        super().__init__(
            message=message,
            details=details,
            code=DomainErrorCode.INVALID_SCOPE,
        )


class MockConflictError(DomainError):
    """Error raised when mocks conflict with each other."""

    def __init__(
        self,
        message: str = "Mock conflicts with an existing mock",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Creates a mock conflict error.

        Args:
            message: Readable error description.
            details: Additional error details.
        """
        super().__init__(
            code=DomainErrorCode.MOCK_CONFLICT,
            message=message,
            details=details or {},
        )
