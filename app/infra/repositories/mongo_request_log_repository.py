"""MongoDB repository implementation for request logs."""

from beanie import SortDirection

from app.domain.request_logs.models import RequestLogRecord
from app.infra.db.mongo.documents import RequestLogDocument
from app.infra.mappers import RequestLogMapper


class MongoRequestLogRepository:
    """Persists and reads request log records from MongoDB."""

    async def write(self, record: RequestLogRecord) -> RequestLogRecord:
        """Persists a request log record and returns it with an id.

        Args:
            record: Request log record to persist.

        Returns:
            Persisted request log record.
        """
        document = RequestLogMapper.to_document(record)
        await document.insert()
        return RequestLogMapper.to_domain(document)

    async def list_records(self, limit: int = 100, offset: int = 0) -> list[RequestLogRecord]:
        """Returns request log records sorted by creation time with pagination.

        Args:
            limit: Maximum number of records to return.
            offset: Number of records to skip.

        Returns:
            Request log records.
        """
        documents = (
            await RequestLogDocument.find_all()
            .sort(
                [("created_at", SortDirection.DESCENDING)],
            )
            .skip(offset)
            .limit(limit)
            .to_list()
        )
        return [RequestLogMapper.to_domain(document) for document in documents]

    async def clear(self) -> None:
        """Deletes all request log records."""
        await RequestLogDocument.find_all().delete()
