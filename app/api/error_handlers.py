import logging
from typing import Any, cast

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.application.exceptions import (
    ApplicationError,
    MockNotFoundError,
    OperationNotAllowedError,
    ResourceAlreadyExistsError,
    ValidationError,
)
from app.domain.mocks import DomainError, MockConflictError
from app.infra.exceptions import InfrastructureError

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(MockNotFoundError, mock_not_found_handler)
    app.add_exception_handler(MockConflictError, mock_conflict_handler)
    app.add_exception_handler(DomainError, domain_error_handler)
    app.add_exception_handler(ApplicationError, application_error_handler)
    app.add_exception_handler(InfrastructureError, infrastructure_error_handler)
    app.add_exception_handler(Exception, unknown_error_handler)


async def mock_not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    error = cast(MockNotFoundError, exc)
    _log_handled_exception(logging.INFO, request, error, status.HTTP_404_NOT_FOUND)
    return _error_response(status.HTTP_404_NOT_FOUND, error)


async def mock_conflict_handler(request: Request, exc: Exception) -> JSONResponse:
    error = cast(MockConflictError, exc)
    _log_handled_exception(logging.WARNING, request, error, status.HTTP_409_CONFLICT)
    return _error_response(status.HTTP_409_CONFLICT, error)


async def domain_error_handler(request: Request, exc: Exception) -> JSONResponse:
    error = cast(DomainError, exc)
    _log_handled_exception(logging.WARNING, request, error, status.HTTP_400_BAD_REQUEST)
    return _error_response(status.HTTP_400_BAD_REQUEST, error)


async def application_error_handler(request: Request, exc: Exception) -> JSONResponse:
    error = cast(ApplicationError, exc)
    if isinstance(error, ValidationError):
        status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    elif isinstance(error, ResourceAlreadyExistsError):
        status_code = status.HTTP_409_CONFLICT
    elif isinstance(error, OperationNotAllowedError):
        status_code = status.HTTP_409_CONFLICT if error.conflict else status.HTTP_400_BAD_REQUEST
    else:
        status_code = status.HTTP_400_BAD_REQUEST

    _log_handled_exception(logging.WARNING, request, error, status_code)
    return _error_response(status_code, error)


async def infrastructure_error_handler(request: Request, exc: Exception) -> JSONResponse:
    error = cast(InfrastructureError, exc)
    _log_handled_exception(logging.ERROR, request, error, status.HTTP_500_INTERNAL_SERVER_ERROR)
    return _error_response(status.HTTP_500_INTERNAL_SERVER_ERROR, error)


async def unknown_error_handler(request: Request, exc: Exception) -> JSONResponse:
    request.state.exception_logged = True
    logger.error(
        "unexpected_exception",
        extra={
            "method": request.method,
            "path": request.url.path,
            "query": request.url.query,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        },
        exc_info=(type(exc), exc, exc.__traceback__),
    )
    return _error_response(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="INTERNAL_SERVER_ERROR",
        message="Internal server error",
        details={},
    )


def _log_handled_exception(
    level: int,
    request: Request,
    exc: DomainError | ApplicationError | InfrastructureError,
    status_code: int,
) -> None:
    logger.log(
        level,
        "handled_exception",
        extra={
            "method": request.method,
            "path": request.url.path,
            "query": request.url.query,
            "status_code": status_code,
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "error_code": str(exc.code),
            "details": exc.details,
        },
    )


def _error_response(
    status_code: int,
    exc: DomainError | ApplicationError | InfrastructureError | None = None,
    *,
    code: str | None = None,
    message: str | None = None,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
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
