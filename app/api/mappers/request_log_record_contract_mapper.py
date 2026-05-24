"""Маппер между доменными записями журнала запросов и API контрактами."""

from app.api.contracts.request_logs.items import (
    MatchedMockItem,
    RequestContextItem,
    RequestLogRecordItem,
)
from app.domain.request_logs.models import RequestLogRecord


class RequestLogRecordContractMapper:
    """Преобразует записи журнала запросов в RESPONSE DTO ответа."""

    @staticmethod
    def from_domain_request_log_record_model(record: RequestLogRecord) -> RequestLogRecordItem:
        """Преобразует доменную запись журнала в RESPONSE DTO ответа."""
        return RequestLogRecordItem(
            id=record.id or "",
            request_context=RequestContextItem(
                id=record.request_context.id,
                method=record.request_context.method,
                path=record.request_context.path,
                headers=record.request_context.headers,
                query_params=record.request_context.query_params,
                body=record.request_context.body,
                timestamp=record.request_context.timestamp,
            ),
            matched_mock=(
                MatchedMockItem(
                    id=record.matched_mock.id,
                    name=record.matched_mock.name,
                    path=record.matched_mock.path,
                    method=record.matched_mock.method,
                    scope=record.matched_mock.scope,
                    response_status_code=record.matched_mock.response_status_code,
                    response_body=record.matched_mock.response_body,
                )
                if record.matched_mock is not None
                else None
            ),
            scope=record.scope,
            response_status_code=record.response_status_code,
            created_at=record.created_at,
        )
