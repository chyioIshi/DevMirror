"""Application service for request log operations."""

import logging

from app.domain.mocks.models.resolution import ResolvedMock
from app.domain.request_contexts import RequestContext
from app.domain.request_logs import RequestLogRepository
from app.domain.request_logs.models import (
    MatchedMock,
    RequestLogRecord,
    RequestLogVerificationExpectation,
    RequestLogVerificationResult,
)

logger = logging.getLogger(__name__)


class RequestLogService:
    """Provides read, clear, create, and verification operations for request logs."""

    def __init__(
        self,
        request_log_repository: RequestLogRepository,
    ) -> None:
        """Initializes the service with a request log repository.

        Args:
            request_log_repository: Repository used to persist and read request log records.
        """
        self._request_log_repository = request_log_repository

    async def create_record(
        self,
        *,
        request_context: RequestContext,
        scope: str,
        resolved_mock: ResolvedMock | None,
    ) -> None:
        """Persists a record for an incoming request and its resolution result.

        Args:
            request_context: Incoming request context.
            scope: Scope resolved for the request.
            resolved_mock: Resolved mock or ``None`` when no mock matched.
        """
        matched_mock = None
        response_status_code = None
        if resolved_mock is not None:
            matched_mock = MatchedMock(
                id=resolved_mock.mock.id or "",
                name=resolved_mock.mock.name,
                path=resolved_mock.mock.path,
                method=resolved_mock.mock.method,
                scope=resolved_mock.mock.scope,
                response_status_code=resolved_mock.mock.response.status_code,
                response_body=resolved_mock.mock.response.body,
            )
            response_status_code = resolved_mock.mock.response.status_code

        await self._request_log_repository.write(
            RequestLogRecord(
                request_context=request_context,
                matched_mock=matched_mock,
                scope=scope,
                response_status_code=response_status_code,
            ),
        )
        matched_mock_name = matched_mock.name if matched_mock else None
        logger.debug(
            (
                f"Запись журнала создана для запроса {request_context.method} "
                f"{request_context.path} в scope {scope} с моком {matched_mock_name}"
            ),
            extra={
                "method": str(request_context.method),
                "path": request_context.path,
                "scope": scope,
                "matched_mock_id": matched_mock.id if matched_mock else None,
            },
        )

    async def list_records(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[RequestLogRecord]:
        """Returns request log records with pagination support.

        Args:
            limit: Maximum number of records to return.
            offset: Number of records to skip.

        Returns:
            Request log records.
        """
        records = await self._request_log_repository.list_records(
            limit=limit,
            offset=offset,
        )
        logger.debug(
            f"Получено {len(records)} записей журнала запросов с limit={limit} и offset={offset}",
            extra={"count": len(records), "limit": limit, "offset": offset},
        )
        return records

    async def clear(self) -> None:
        """Completely clears the request log."""
        await self._request_log_repository.clear()
        logger.info("Журнал запросов очищен")

    async def verify(
        self,
        expectation: RequestLogVerificationExpectation,
    ) -> RequestLogVerificationResult:
        """Checks whether the log contains the expected number of requests.

        Args:
            expectation: Verification expectation to match against request log records.

        Returns:
            Verification result with match status and actual count.
        """
        records = await self._request_log_repository.list_records()
        actual_count = sum(1 for record in records if record.matches_expectation(expectation))
        matched = (
            actual_count > 0
            if expectation.expected_count is None
            else actual_count == expectation.expected_count
        )
        result = RequestLogVerificationResult(
            matched=matched,
            actual_count=actual_count,
        )
        logger.info(
            (
                f"Проверка журнала запросов завершена: matched={result.matched}, "
                f"actual_count={result.actual_count}, "
                f"expected_count={expectation.expected_count}"
            ),
            extra={
                "matched": result.matched,
                "actual_count": result.actual_count,
                "expected_count": expectation.expected_count,
            },
        )
        return result
