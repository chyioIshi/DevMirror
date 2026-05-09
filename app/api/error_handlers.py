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


async def mock_not_found_handler(request: Request, exc: MockNotFoundError) -> JSONResponse:
    _log_handled_exception(logging.INFO, request, exc, status.HTTP_404_NOT_FOUND)
    return _error_response(status.HTTP_404_NOT_FOUND, exc)


async def mock_conflict_handler(request: Request, exc: MockConflictError) -> JSONResponse:
    _log_handled_exception(logging.WARNING, request, exc, status.HTTP_409_CONFLICT)
    return _error_response(status.HTTP_409_CONFLICT, exc)


async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    _log_handled_exception(logging.WARNING, request, exc, status.HTTP_400_BAD_REQUEST)
    return _error_response(status.HTTP_400_BAD_REQUEST, exc)


async def application_error_handler(request: Request, exc: ApplicationError) -> JSONResponse:
    if isinstance(exc, ValidationError):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    elif isinstance(exc, ResourceAlreadyExistsError):
        status_code = status.HTTP_409_CONFLICT
    elif isinstance(exc, OperationNotAllowedError):
        status_code = status.HTTP_409_CONFLICT if exc.conflict else status.HTTP_400_BAD_REQUEST
    else:
        status_code = status.HTTP_400_BAD_REQUEST

    _log_handled_exception(logging.WARNING, request, exc, status_code)
    return _error_response(status_code, exc)


async def infrastructure_error_handler(request: Request, exc: InfrastructureError) -> JSONResponse:
    _log_handled_exception(logging.ERROR, request, exc, status.HTTP_500_INTERNAL_SERVER_ERROR)
    return _error_response(status.HTTP_500_INTERNAL_SERVER_ERROR, exc)


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
