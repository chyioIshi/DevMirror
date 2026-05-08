import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.application.exceptions import (
    ApplicationError,
    MockNotFoundError,
    OperationNotAllowedError,
    ResourceAlreadyExistsError,
    ValidationError,
)
from app.domain.mocks.exceptions import DomainError, MockConflictError
from app.infra.exceptions import InfrastructureError

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """Регистрирует хендлеры исключений приложения."""

    app.add_exception_handler(MockNotFoundError, mock_not_found_handler)
    app.add_exception_handler(MockConflictError, mock_conflict_handler)
    app.add_exception_handler(DomainError, domain_error_handler)
    app.add_exception_handler(ApplicationError, application_error_handler)
    app.add_exception_handler(InfrastructureError, infrastructure_error_handler)
    app.add_exception_handler(Exception, unknown_error_handler)


async def mock_not_found_handler(request: Request, exc: MockNotFoundError) -> JSONResponse:
    """Логирует ошибку domain слоя (конкретно отсутствие мока) и возвращает HTTP 404."""

    logger.error(
        "Mock not found error on %s %s",
        request.method,
        request.url.path,
        exc_info=(type(exc), exc, exc.__traceback__),
    )

    return _error_response(status.HTTP_404_NOT_FOUND, exc)


async def mock_conflict_handler(request: Request, exc: MockConflictError) -> JSONResponse:
    """Логирует ошибку domain слоя (конкретно конфликт моков) и возвращает HTTP 409."""

    logger.error(
        "Mock conflict error on %s %s",
        request.method,
        request.url.path,
        exc_info=(type(exc), exc, exc.__traceback__),
    )

    return _error_response(status.HTTP_409_CONFLICT, exc)


async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    """Логирует ошибку domain слоя и возвращает HTTP 400."""

    logger.error(
        "Domain error on %s %s",
        request.method,
        request.url.path,
        exc_info=(type(exc), exc, exc.__traceback__),
    )

    return _error_response(status.HTTP_400_BAD_REQUEST, exc)


async def application_error_handler(request: Request, exc: ApplicationError) -> JSONResponse:
    """Логирует ошибку application слоя и возвращает HTTP 422 | 409 | 400
    в зависимости от ошибки."""

    logger.error(
        "Service error on %s %s",
        request.method,
        request.url.path,
        exc_info=(type(exc), exc, exc.__traceback__),
    )

    if isinstance(exc, ValidationError):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    elif isinstance(exc, ResourceAlreadyExistsError):
        status_code = status.HTTP_409_CONFLICT
    elif isinstance(exc, OperationNotAllowedError):
        status_code = status.HTTP_409_CONFLICT if exc.conflict else status.HTTP_400_BAD_REQUEST
    else:
        status_code = status.HTTP_400_BAD_REQUEST

    return _error_response(status_code, exc)


async def infrastructure_error_handler(request: Request, exc: InfrastructureError) -> JSONResponse:
    """Логирует ошибку инфра слоя и возвращает HTTP 500."""

    logger.error(
        "Infrastructure error on %s %s",
        request.method,
        request.url.path,
        exc_info=(type(exc), exc, exc.__traceback__),
    )
    return _error_response(status.HTTP_500_INTERNAL_SERVER_ERROR, exc)


async def unknown_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Логирует непредвиденную ошибку и возвращает HTTP 500."""

    logger.error(
        "Unhandled error on %s %s",
        request.method,
        request.url.path,
        exc_info=(type(exc), exc, exc.__traceback__),
    )
    return _error_response(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="INTERNAL_SERVER_ERROR",
        message="Internal server error",
        details={},
    )


def _error_response(
    status_code: int,
    exc: DomainError | ApplicationError | InfrastructureError | None = None,
    *,
    code: str | None = None,
    message: str | None = None,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    """Создает единый JSON-ответ с кодом, сообщением и деталями ошибки."""

    if exc is not None:
        code = str(exc.code)
        message = exc.message
        details = exc.details

    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
            },
        },
    )
