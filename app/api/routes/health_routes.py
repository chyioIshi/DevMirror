
from fastapi import APIRouter

from app.api.contracts.health import HealthResponse

health_router = APIRouter(tags=["health"])


@health_router.get("", response_model=HealthResponse)
async def healthcheck() -> HealthResponse:
    return HealthResponse(status="ok")
