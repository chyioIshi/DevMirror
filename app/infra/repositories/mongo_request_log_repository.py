from pymongo import DESCENDING

from app.domain.request_logs.models.request_log_record import RequestLogRecord
from app.infra.db.mongo.documents.request_log_document import RequestLogDocument
from app.infra.mappers.request_log_mapper import RequestLogMapper


class MongoRequestLogRepository:
    """Сохраняет и читает журнал запросов в MongoDB."""

    async def write(self, record: RequestLogRecord) -> RequestLogRecord:
        """Сохраняет запись журнала запросов и возвращает её с id."""
        document = RequestLogMapper.to_document(record)
        await document.insert()
        return RequestLogMapper.to_domain(document)

    async def list_records(self, limit: int = 100, offset: int = 0) -> list[RequestLogRecord]:
        """Возвращает записи журнала в порядке от новых к старым с поддержкой пагинации."""
        documents = await RequestLogDocument.find_all().sort(
            [("created_at", DESCENDING)],
        ).skip(offset).limit(limit).to_list()
        return [RequestLogMapper.to_domain(document) for document in documents]

    async def clear(self) -> None:
        """Удаляет все записи журнала запросов."""
        await RequestLogDocument.find_all().delete()
