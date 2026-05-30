"""Catch-all route for handling user requests to mocks."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.application.services import MockResolverService
from app.config import AppSettings
from app.di import (
    get_app_settings,
    get_mock_resolver_service,
    get_mock_response_builder,
    get_request_context_resolver,
)
from app.domain.mocks.models.resolution import ResolvedMock
from app.infra.context import RequestContextResolver
from app.infra.response import MockResponseBuilder

catch_all_router = APIRouter(tags=["catch-all"])


def _reserved_paths(settings: AppSettings) -> tuple[str, ...]:
    """Returns service routes that must not be intercepted by catch-all.

    Args:
        settings: Application settings containing service route prefixes.

    Returns:
        Tuple of reserved path prefixes and exact service paths.
    """
    return (
        settings.admin_prefix,
        settings.request_log_prefix,
        settings.health_prefix,
        "/openapi.json",
        "/favicon.ico",
        "/docs",
        "/redoc",
    )


def _is_reserved_path(path: str, settings: AppSettings) -> bool:
    """Checks whether a path belongs to service routes.

    Args:
        path: Incoming request path.
        settings: Application settings containing service route prefixes.

    Returns:
        True if the path is reserved for service endpoints, otherwise False.
    """
    reserved_paths = _reserved_paths(settings)
    if path in reserved_paths:
        return True
    return any(path == prefix or path.startswith(f"{prefix}/") for prefix in reserved_paths)  # noqa: E501


@catch_all_router.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def catch_each_request(
    request: Request,
    settings: Annotated[AppSettings, Depends(get_app_settings)],
    request_context_resolver: Annotated[
        RequestContextResolver,
        Depends(get_request_context_resolver),
    ],
    mock_resolver_service: Annotated[
        MockResolverService,
        Depends(get_mock_resolver_service),
    ],
    mock_response_builder: Annotated[
        MockResponseBuilder,
        Depends(get_mock_response_builder),
    ],
) -> Response:
    """Handles an incoming request and returns the matched mock response.

    Args:
        request: Original FastAPI request.
        settings: Application config.
        request_context_resolver: Adapter that builds the domain request context.
        mock_resolver_service: Service that resolves a matching mock.
        mock_response_builder: Adapter that builds an HTTP response from a mock.

    Returns:
        HTTP response built from the matched mock.

    Raises:
        HTTPException: If the path is reserved or no matching active mock is found.
    """
    if _is_reserved_path(request.url.path, settings):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not this route!!!")  # noqa: E501

    request_context = await request_context_resolver.resolve(request)
    resolved_mock: ResolvedMock | None = await mock_resolver_service.resolve(request_context)  # noqa: E501
    if resolved_mock is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active mock matched the request",
        )

    return mock_response_builder.build(resolved_mock.mock)
