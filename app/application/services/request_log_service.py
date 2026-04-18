
from app.domain.mocks.models.resolution.resolved_mock import ResolvedMock
from app.domain.request_contexts.models.request_context import RequestContext
from app.domain.request_logs.models import (
    MatchedMock,
    RequestLogRecord,
    RequestLogVerificationExpectation,
    RequestLogVerificationResult,
)
from app.domain.request_logs.repository import RequestLogRepository


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

    async def list_records(
        self, limit: int = 100, offset: int = 0,
    ) -> list[RequestLogRecord]:
        """Возвращает записи журнала запросов с поддержкой пагинации."""
        return await self._request_log_repository.list_records(
            limit=limit, offset=offset,
        )

    async def clear(self) -> None:
        """Полностью очищает журнал запросов."""
        await self._request_log_repository.clear()

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
        return RequestLogVerificationResult(
            matched=matched,
            actual_count=actual_count,
        )
