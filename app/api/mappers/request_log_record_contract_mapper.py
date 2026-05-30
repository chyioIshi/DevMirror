"""Mapper between domain request log records and API contracts."""

from app.api.contracts.request_logs.items import (
    MatchedMockItem,
    RequestContextItem,
    RequestLogRecordItem,
)
from app.domain.request_logs.models import RequestLogRecord


class RequestLogRecordContractMapper:
    """Converts request log records to response DTOs."""

    @staticmethod
    def from_domain_request_log_record_model(record: RequestLogRecord) -> RequestLogRecordItem:  # noqa: E501
        """Converts a domain request log record to a response DTO.

        Args:
            record: Domain request log record.

        Returns:
            API response DTO for the request log record.
        """
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
