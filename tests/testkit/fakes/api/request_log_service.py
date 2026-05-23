from app.domain.request_logs.models import RequestLogRecord
from app.domain.request_logs.models.verification import (
    RequestLogVerificationExpectation,
    RequestLogVerificationResult,
)


class FakeRequestLogService:
    """Fake RequestLogService для integration-тестов API routes."""

    def __init__(
        self,
        *,
        records: list[RequestLogRecord] | None = None,
        verification_result: RequestLogVerificationResult | None = None,
    ) -> None:
        self.records = records or []
        self.verification_result = verification_result or RequestLogVerificationResult(
            matched=True,
            actual_count=len(self.records),
        )
        self.list_records_calls: list[tuple[int, int]] = []
        self.verify_calls: list[RequestLogVerificationExpectation] = []
        self.clear_calls = 0
        self.list_records_error: Exception | None = None
        self.verify_error: Exception | None = None
        self.clear_error: Exception | None = None

    async def list_records(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[RequestLogRecord]:
        """Возвращает заранее заданные записи журнала."""
        self.list_records_calls.append((limit, offset))
        if self.list_records_error is not None:
            raise self.list_records_error
        return self.records

    async def verify(
        self,
        expectation: RequestLogVerificationExpectation,
    ) -> RequestLogVerificationResult:
        """Возвращает заранее заданный результат проверки."""
        self.verify_calls.append(expectation)
        if self.verify_error is not None:
            raise self.verify_error
        return self.verification_result

    async def clear(self) -> None:
        """Запоминает вызов очистки журнала."""
        self.clear_calls += 1
        if self.clear_error is not None:
            raise self.clear_error
