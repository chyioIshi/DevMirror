from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ApplicationErrorCode(StrEnum):
    """Коды ошибок application слоя."""

    MOCK_NOT_FOUND = "MOCK_NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    OPERATION_NOT_ALLOWED = "OPERATION_NOT_ALLOWED"
    RESOURCE_ALREADY_EXISTS = "RESOURCE_ALREADY_EXISTS"
    CONCURRENCY_CONFLICT = "CONCURRENCY_CONFLICT"


@dataclass(eq=False)
class ApplicationError(Exception):
    """Базовая ошибка use case или сервиса."""

    code: ApplicationErrorCode
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        Exception.__init__(self, self.message)


class MockNotFoundError(ApplicationError):
    """Ошибка отсутствия мока при поиске по id."""

    def __init__(
        self,
        message: str = "Mock was not found",
        details: dict[str, Any] | None = None,
        *,
        mock_id: str | None = None,
    ) -> None:
        error_details = dict(details or {})
        if mock_id is not None:
            error_details.setdefault("mock_id", mock_id)
        super().__init__(
            code=ApplicationErrorCode.MOCK_NOT_FOUND,
            message=message,
            details=error_details,
        )


class ValidationError(ApplicationError):
    """Ошибка валидации команды или данных в use case."""

    def __init__(
        self,
        message: str = "Validation error",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code=ApplicationErrorCode.VALIDATION_ERROR,
            message=message,
            details=details or {},
        )


class OperationNotAllowedError(ApplicationError):
    """Ошибка неподдерживаемой операции в текущем application контексте."""

    def __init__(
        self,
        message: str = "Operation is not allowed",
        details: dict[str, Any] | None = None,
        *,
        conflict: bool = False,
    ) -> None:
        self.conflict = conflict
        super().__init__(
            code=ApplicationErrorCode.OPERATION_NOT_ALLOWED,
            message=message,
            details=details or {},
        )


class ResourceAlreadyExistsError(ApplicationError):
    """Ошибка попытки создать ресурс, который уже существует."""

    def __init__(
        self,
        message: str = "Resource already exists",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code=ApplicationErrorCode.RESOURCE_ALREADY_EXISTS,
            message=message,
            details=details or {},
        )


class ConcurrencyConflictError(ApplicationError):
    """Ошибка конфликта конкурентного изменения ресурса."""

    def __init__(
        self,
        message: str = "Concurrency conflict",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code=ApplicationErrorCode.CONCURRENCY_CONFLICT,
            message=message,
            details=details or {},
        )
