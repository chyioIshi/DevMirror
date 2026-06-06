"""Application-layer exceptions and error codes."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ApplicationErrorCode(StrEnum):
    """Application-layer error codes."""

    MOCK_NOT_FOUND = "MOCK_NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    OPERATION_NOT_ALLOWED = "OPERATION_NOT_ALLOWED"
    RESOURCE_ALREADY_EXISTS = "RESOURCE_ALREADY_EXISTS"
    SIDE_EFFECT_PROVIDER_ALREADY_REGISTERED = "SIDE_EFFECT_PROVIDER_ALREADY_REGISTERED"
    SIDE_EFFECT_PROVIDER_NOT_FOUND = "SIDE_EFFECT_PROVIDER_NOT_FOUND"
    SIDE_EFFECT_EXECUTION_FAILED = "SIDE_EFFECT_EXECUTION_FAILED"


@dataclass(eq=False)
class ApplicationError(Exception):
    """Base error for use cases and application services."""

    code: ApplicationErrorCode
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initializes the base `Exception` with the application error message."""
        Exception.__init__(self, self.message)


class MockNotFoundError(ApplicationError):
    """Error raised when a mock cannot be found by id."""

    def __init__(
        self,
        message: str = "Mock was not found",
        details: dict[str, Any] | None = None,
        *,
        mock_id: str | None = None,
    ) -> None:
        """Creates a mock-not-found error.

        Args:
            message: Human-readable error description.
            details: Additional error details.
            mock_id: Optional mock id added to error details.
        """
        error_details = dict(details or {})
        if mock_id is not None:
            error_details.setdefault("mock_id", mock_id)
        super().__init__(
            code=ApplicationErrorCode.MOCK_NOT_FOUND,
            message=message,
            details=error_details,
        )


class ValidationError(ApplicationError):
    """Error raised when command or use-case data is invalid."""

    def __init__(
        self,
        message: str = "Validation error",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Creates a validation error.

        Args:
            message: Human-readable error description.
            details: Additional error details.
        """
        super().__init__(
            code=ApplicationErrorCode.VALIDATION_ERROR,
            message=message,
            details=details or {},
        )


class OperationNotAllowedError(ApplicationError):
    """Error raised when an operation is not allowed in the current application context."""

    def __init__(
        self,
        message: str = "Operation is not allowed",
        details: dict[str, Any] | None = None,
        *,
        conflict: bool = False,
    ) -> None:
        """Creates an operation-not-allowed error.

        Args:
            message: Human-readable error description.
            details: Additional error details.
            conflict: Whether the error should be treated as a conflict.
        """
        self.conflict = conflict
        super().__init__(
            code=ApplicationErrorCode.OPERATION_NOT_ALLOWED,
            message=message,
            details=details or {},
        )


class ResourceAlreadyExistsError(ApplicationError):
    """Error raised when trying to create a resource that already exists."""

    def __init__(
        self,
        message: str = "Resource already exists",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Creates a resource-already-exists error.

        Args:
            message: Human-readable error description.
            details: Additional error details.
        """
        super().__init__(
            code=ApplicationErrorCode.RESOURCE_ALREADY_EXISTS,
            message=message,
            details=details or {},
        )


class SideEffectProviderAlreadyRegisteredError(ApplicationError):
    """Error raised when registering a duplicate side effect provider."""

    def __init__(
        self,
        message: str = "Side effect provider is already registered",
        details: dict[str, Any] | None = None,
        *,
        provider: str | None = None,
    ) -> None:
        """Creates a duplicate side effect provider registration error."""
        error_details = dict(details or {})
        if provider is not None:
            error_details.setdefault("provider", provider)
        super().__init__(
            code=ApplicationErrorCode.SIDE_EFFECT_PROVIDER_ALREADY_REGISTERED,
            message=message,
            details=error_details,
        )


class SideEffectProviderNotFoundError(ApplicationError):
    """Error raised when no side effect provider is registered for a name."""

    def __init__(
        self,
        message: str = "Side effect provider was not found",
        details: dict[str, Any] | None = None,
        *,
        provider: str | None = None,
    ) -> None:
        """Creates an unknown side effect provider error."""
        error_details = dict(details or {})
        if provider is not None:
            error_details.setdefault("provider", provider)
        super().__init__(
            code=ApplicationErrorCode.SIDE_EFFECT_PROVIDER_NOT_FOUND,
            message=message,
            details=error_details,
        )


class SideEffectExecutionFailedError(ApplicationError):
    """Error raised when a side effect cannot be executed successfully."""

    def __init__(
        self,
        message: str = "Side effect execution failed",
        details: dict[str, Any] | None = None,
        *,
        provider: str | None = None,
        attempts: int | None = None,
    ) -> None:
        """Creates a side effect execution failure error."""
        error_details = dict(details or {})
        if provider is not None:
            error_details.setdefault("provider", provider)
        if attempts is not None:
            error_details.setdefault("attempts", attempts)
        super().__init__(
            code=ApplicationErrorCode.SIDE_EFFECT_EXECUTION_FAILED,
            message=message,
            details=error_details,
        )
