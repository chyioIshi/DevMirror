import logging

from app.domain.mocks.models.resolution.resolved_mock import ResolvedMock
from app.domain.request_contexts.models.request_context import RequestContext
from app.domain.request_logs.models import (
    MatchedMock,
    RequestLogRecord,
    RequestLogVerificationExpectation,
    RequestLogVerificationResult,
)
from app.domain.request_logs.repository import RequestLogRepository

logger = logging.getLogger(__name__)


class RequestLogService:
    """Предоставляет операции чтения, очистки и проверки журнала запросов."""

    def __init__(
        self, request_log_repository: RequestLogRepository,
    ) -> None:
        """Инициализирует сервис репозиторием журнала запросов."""
        self._request_log_repository = request_log_repository

    async def create_record(
        self,
        *,
        request_context: RequestContext,
        scope: str,
        resolved_mock: ResolvedMock | None,
    ) -> None:
        """Сохраняет запись о входящем запросе и результате резолвинга."""
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
        logger.debug(
            f"Запись журнала создана для запроса {request_context.method} {request_context.path} в scope {scope} с моком {matched_mock.name if matched_mock else None}",
            extra={
                "method": str(request_context.method),
                "path": request_context.path,
                "scope": scope,
                "matched_mock_id": matched_mock.id if matched_mock else None,
            },
        )

    async def list_records(
        self, limit: int = 100, offset: int = 0,
    ) -> list[RequestLogRecord]:
        """Возвращает записи журнала запросов с поддержкой пагинации."""
        records = await self._request_log_repository.list_records(
            limit=limit, offset=offset,
        )
        logger.debug(
            f"Получено {len(records)} записей журнала запросов с limit={limit} и offset={offset}",
            extra={"count": len(records), "limit": limit, "offset": offset},
        )
        return records

    async def clear(self) -> None:
        """Полностью очищает журнал запросов."""
        await self._request_log_repository.clear()
        logger.info("Журнал запросов очищен")

    async def verify(
        self,
        expectation: RequestLogVerificationExpectation,
    ) -> RequestLogVerificationResult:
        """Проверяет, что журнал содержит ожидаемое количество запросов."""
        records = await self._request_log_repository.list_records()
        actual_count = sum(
            1 for record in records if record.matches_expectation(expectation)
        )
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
            f"Проверка журнала запросов завершена: matched={result.matched}, actual_count={result.actual_count}, expected_count={expectation.expected_count}",
            extra={
                "matched": result.matched,
                "actual_count": result.actual_count,
                "expected_count": expectation.expected_count,
            },
        )
        return result
