"""Registration and implementation of HTTP error handlers."""

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
    """Registers handlers for domain, application, and infrastructure errors.

    Args:
        app: FastAPI instance where exception handlers are added.
    """
    app.add_exception_handler(MockNotFoundError, mock_not_found_handler)
    app.add_exception_handler(MockConflictError, mock_conflict_handler)
    app.add_exception_handler(DomainError, domain_error_handler)
    app.add_exception_handler(ApplicationError, application_error_handler)
    app.add_exception_handler(InfrastructureError, infrastructure_error_handler)
    app.add_exception_handler(Exception, unknown_error_handler)


async def mock_not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    """Converts a missing mock error to HTTP 404.

    Args:
        request: Incoming HTTP request.
        exc: Exception passed by FastAPI to the handler.

    Returns:
        JSON response with error details.
    """
    error = cast(MockNotFoundError, exc)
    _log_handled_exception(logging.INFO, request, error, status.HTTP_404_NOT_FOUND)
    return _error_response(status.HTTP_404_NOT_FOUND, error)


async def mock_conflict_handler(request: Request, exc: Exception) -> JSONResponse:
    """Converts a mock conflict error to HTTP 409.

    Args:
        request: Incoming HTTP request.
        exc: Exception passed by FastAPI to the handler.

    Returns:
        JSON response with error details.
    """
    error = cast(MockConflictError, exc)
    _log_handled_exception(logging.WARNING, request, error, status.HTTP_409_CONFLICT)
    return _error_response(status.HTTP_409_CONFLICT, error)


async def domain_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Converts a domain error to HTTP 400.

    Args:
        request: Incoming HTTP request.
        exc: Exception passed by FastAPI to the handler.

    Returns:
        JSON response with error details.
    """
    error = cast(DomainError, exc)
    _log_handled_exception(logging.WARNING, request, error, status.HTTP_400_BAD_REQUEST)
    return _error_response(status.HTTP_400_BAD_REQUEST, error)


async def application_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Converts an application error to the appropriate HTTP status.

    Args:
        request: Incoming HTTP request.
        exc: Exception passed by FastAPI to the handler.

    Returns:
        JSON response with error details.
    """
    error = cast(ApplicationError, exc)
    if isinstance(error, ValidationError):
        status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    elif isinstance(error, ResourceAlreadyExistsError):
        status_code = status.HTTP_409_CONFLICT
    elif isinstance(error, OperationNotAllowedError):
        status_code = status.HTTP_409_CONFLICT if error.conflict else status.HTTP_400_BAD_REQUEST  # noqa: E501
    else:
        status_code = status.HTTP_400_BAD_REQUEST

    _log_handled_exception(logging.WARNING, request, error, status_code)
    return _error_response(status_code, error)


async def infrastructure_error_handler(request: Request, exc: Exception) -> JSONResponse:  # noqa: E501
    """Converts an infrastructure error to HTTP 500.

    Args:
        request: Incoming HTTP request.
        exc: Exception passed by FastAPI to the handler.

    Returns:
        JSON response with error details.
    """
    error = cast(InfrastructureError, exc)
    _log_handled_exception(logging.ERROR, request, error, status.HTTP_500_INTERNAL_SERVER_ERROR)  # noqa: E501
    return _error_response(status.HTTP_500_INTERNAL_SERVER_ERROR, error)


async def unknown_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Logs an unexpected error and returns a safe HTTP 500.

    Args:
        request: Incoming HTTP request.
        exc: Unhandled exception.

    Returns:
        JSON response without internal error details.
    """
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
    """Logs an error handled at the HTTP boundary.

    Args:
        level: Logging level.
        request: Incoming HTTP request.
        exc: Domain, application, or infrastructure error.
        status_code: HTTP status returned to the client.
    """
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
    """Builds a unified JSON response for API errors.

    Args:
        status_code: HTTP response status.
        exc: Typed application error.
        code: Error code used when `exc` is not provided.
        message: Error message used when `exc` is not provided.
        details: Additional error details.

    Returns:
        JSON response in the unified error format.
    """
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
