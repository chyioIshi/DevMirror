from typing import Protocol

from app.domain.request_logs.models.request_log_record import RequestLogRecord


class RequestLogRepository(Protocol):
    """Описывает операции хранения и чтения журнала запросов."""

    async def write(self, record: RequestLogRecord) -> RequestLogRecord:
        """Сохраняет запись журнала запросов."""
        ...

    async def list_records(self, limit: int = 100, offset: int = 0) -> list[RequestLogRecord]:
        """Возвращает записи журнала запросов с поддержкой пагинации."""
        ...

    async def clear(self) -> None:
        """Очищает журнал запросов."""
        ...
