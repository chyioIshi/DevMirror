from app.domain.request_logs.models import RequestLogRecord

type ListRecordsCall = tuple[int, int]


class FakeRequestLogRepository:
    """In-memory fake RequestLogRepository для application-тестов."""

    def __init__(self, records: list[RequestLogRecord] | None = None) -> None:
        self.records: list[RequestLogRecord] = list(records or [])
        self.written_records: list[RequestLogRecord] = []
        self.list_records_calls: list[ListRecordsCall] = []
        self.clear_calls = 0

    async def write(self, record: RequestLogRecord) -> RequestLogRecord:
        """Сохраняет запись журнала."""
        self.records.append(record)
        self.written_records.append(record)
        return record

    async def list_records(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[RequestLogRecord]:
        """Возвращает записи журнала с пагинацией."""
        self.list_records_calls.append((limit, offset))
        return self.records[offset : offset + limit]

    async def clear(self) -> None:
        """Очищает записи журнала."""
        self.clear_calls += 1
        self.records.clear()

