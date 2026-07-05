"""Catch-all route for handling user requests to mocks."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from fastapi.routing import APIRoute
from starlette.routing import Match
from starlette.types import Scope

import app.config as app_config
from app.application.mocks import MockResolverService
from app.application.side_effects import SideEffectExecutionService
from app.config import AppSettings
from app.di import (
    get_mock_resolver_service,
    get_mock_response_builder,
    get_request_context_resolver,
    get_side_effect_execution_service,
)
from app.domain.mocks.models.resolution import ResolvedMock
from app.infra.context import RequestContextResolver
from app.infra.response import MockResponseBuilder


class MockCatchAllRoute(APIRoute):
    """Catch-all route that skips service paths before endpoint execution."""

    def matches(self, scope: Scope) -> tuple[Match, Scope]:
        """Skips the route when the incoming path belongs to service APIs."""
        path = str(scope.get("path", ""))
        if self.is_reserved_path(path):
            return Match.NONE, {}
        return super().matches(scope)

    @staticmethod
    def is_reserved_path(path: str) -> bool:
        """Checks whether the path belongs to service APIs."""
        reserved_paths = MockCatchAllRoute._reserved_paths(app_config.get_app_settings())
        return any(
            path == reserved_path or path.startswith(f"{reserved_path}/")
            for reserved_path in reserved_paths
        )

    @staticmethod
    def _reserved_paths(settings: AppSettings) -> tuple[str, ...]:
        return (
            settings.admin_prefix,
            settings.request_log_prefix,
            settings.health_prefix,
            settings.openapi_url,
            settings.favicon_path,
            settings.docs_url,
            settings.redoc_url,
        )


catch_all_router = APIRouter(route_class=MockCatchAllRoute, tags=["catch-all"])


@catch_all_router.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def catch_each_request(
    request: Request,
    request_context_resolver: Annotated[
        RequestContextResolver,
        Depends(get_request_context_resolver),
    ],
    mock_resolver_service: Annotated[
        MockResolverService,
        Depends(get_mock_resolver_service),
    ],
    side_effect_execution_service: Annotated[
        SideEffectExecutionService,
        Depends(get_side_effect_execution_service),
    ],
    mock_response_builder: Annotated[
        MockResponseBuilder,
        Depends(get_mock_response_builder),
    ],
) -> Response:
    """Handles an incoming request and returns the matched mock response.

    Args:
        request: Original FastAPI request.
        request_context_resolver: Adapter that builds the domain request context.
        mock_resolver_service: Service that resolves a matching mock.
        side_effect_execution_service: Service that executes response side effects.
        mock_response_builder: Adapter that builds an HTTP response from a mock.

    Returns:
        HTTP response built from the matched mock.
    """
    request_context = await request_context_resolver.resolve(request)
    resolved_mock: ResolvedMock = await mock_resolver_service.resolve(request_context)

    mock_response = resolved_mock.mock.response
    await side_effect_execution_service.execute(
        side_effects=mock_response.side_effects,
        request=request_context,
        mock=resolved_mock.mock,
        response=mock_response,
    )
    return mock_response_builder.build_response(mock_response)
