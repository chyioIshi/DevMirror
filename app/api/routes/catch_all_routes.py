
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.application.services.mock_resolver_service import MockResolverService
from app.domain.models.mocks.resolution.resolved_mock import ResolvedMock
from app.infra.response.mock_response_builder import MockResponseBuilder
from app.config import Settings
from app.di import get_app_settings, get_mock_resolver_service, get_mock_response_builder

catch_all_router = APIRouter(tags=["catch-all"])

def _reserved_paths(settings: Settings) -> tuple[str, ...]:
    """Возвращает набор служебных роутов, которые не должен перехватывать catch-all."""
    return (
        settings.admin_prefix,
        settings.request_log_prefix,
        settings.health_prefix,
        "/openapi.json",
        "/favicon.ico",
        "/docs",
        "/redoc",
    )


def _is_reserved_path(path: str, settings: Settings) -> bool:
    """Проверяет, относится ли путь к служебным роутам."""
    reserved_paths = _reserved_paths(settings)
    if path in reserved_paths:
        return True
    return any(path == prefix or path.startswith(f"{prefix}/") for prefix in reserved_paths)


@catch_all_router.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def catch_each_request(
    request: Request,
    settings: Settings = Depends(get_app_settings),
    mock_resolver_service: MockResolverService = Depends(get_mock_resolver_service),
    mock_response_builder: MockResponseBuilder = Depends(get_mock_response_builder),
) -> Response:
    if _is_reserved_path(request.url.path, settings):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not this route!!!")

    resolved_mock: ResolvedMock = await mock_resolver_service.resolve(request)
    if resolved_mock is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active mock matched the request",
        )

    return mock_response_builder.build(resolved_mock.mock)
