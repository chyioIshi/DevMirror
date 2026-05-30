"""Request log repository port."""

from typing import Protocol

from app.domain.request_logs.models import RequestLogRecord


class RequestLogRepository(Protocol):
    """Describes request log persistence and read operations."""

    async def write(self, record: RequestLogRecord) -> RequestLogRecord:
        """Persists a request log record.

        Args:
            record: Request log record to persist.

        Returns:
            Persisted request log record.
        """
        ...

    async def list_records(self, limit: int = 100, offset: int = 0) -> list[RequestLogRecord]:
        """Returns request log records with pagination support.

        Args:
            limit: Maximum number of records to return.
            offset: Number of records to skip.

        Returns:
            Request log records.
        """
        ...

    async def clear(self) -> None:
        """Clears the request log."""
        ...
