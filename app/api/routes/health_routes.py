"""Application healthcheck route."""

from fastapi import APIRouter

from app.api.contracts.health import HealthResponse

health_router = APIRouter(tags=["health"])


@health_router.get("", response_model=HealthResponse)
async def healthcheck() -> HealthResponse:
    """Returns the application health status.

    Returns:
        Healthcheck response with `ok` status.
    """
    return HealthResponse(status="ok")
