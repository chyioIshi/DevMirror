
from fastapi import APIRouter, Body, Depends, Response, status

from app.api.contracts.common.pagination_request import PaginationRequest
from app.api.contracts.request_logs.requests import VerifyRequestLogRequest
from app.api.contracts.request_logs.responses import (
    RequestLogListResponse,
    VerifyRequestLogResponse,
)
from app.application.mappers.request_log_record_contract_mapper import (
    RequestLogRecordContractMapper,
)
from app.application.mappers.request_log_verification_contract_mapper import (
    RequestLogVerificationContractMapper,
)
from app.application.services.request_log_service import RequestLogService
from app.di import get_request_log_service

request_log_router = APIRouter(tags=["request-logs"])

@request_log_router.get("", response_model=RequestLogListResponse)
async def list_request_logs(
    pagination: PaginationRequest = Body(default=PaginationRequest()),
    request_log_service: RequestLogService = Depends(get_request_log_service),
) -> RequestLogListResponse:
    """Возвращает записи журнала запросов с поддержкой пагинации."""
    items = await request_log_service.list_records(limit=pagination.limit, offset=pagination.offset)
    response_items = [
        RequestLogRecordContractMapper.from_domain_request_log_record_model(item)
        for item in items
    ]
    return RequestLogListResponse(items=response_items, total=len(response_items))


@request_log_router.post("/verify", response_model=VerifyRequestLogResponse)
async def verify_request_logs(
    payload: VerifyRequestLogRequest,
    request_log_service: RequestLogService = Depends(get_request_log_service),
) -> VerifyRequestLogResponse:
    """Проверяет, что в журнале есть ожидаемые запросы."""
    result = await request_log_service.verify(
        RequestLogVerificationContractMapper.to_domain_request_log_verification_model(
            payload
        )
    )
    return RequestLogVerificationContractMapper.from_domain_request_log_verification_model(
        result
    )


@request_log_router.delete("", status_code=status.HTTP_200_OK)
async def clear_request_logs(
    request_log_service: RequestLogService = Depends(get_request_log_service),
) -> Response:
    """Очищает журнал запросов."""
    await request_log_service.clear()
    return Response(status_code=status.HTTP_200_OK)
