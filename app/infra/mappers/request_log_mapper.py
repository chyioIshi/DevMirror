
from beanie import PydanticObjectId

from app.domain.request_logs.models.request_log_record import RequestLogRecord
from app.infra.db.mongo.documents.request_log_document import RequestLogDocument


class RequestLogMapper:
    """Преобразует request logs между Mongo-документами и доменными моделями."""

    @staticmethod
    def to_domain(document: RequestLogDocument) -> RequestLogRecord:
        """Преобразует сохранённый Mongo-документ в доменную модель."""
        return RequestLogRecord(
            id=str(document.id),
            request_context=document.request_context,
            matched_mock=document.matched_mock,
            scope=document.scope,
            response_status_code=document.response_status_code,
            created_at=document.created_at,
        )

    @staticmethod
    def to_document(record: RequestLogRecord) -> RequestLogDocument:
        """Преобразует доменную модель в Mongo-документ."""
        document = RequestLogDocument(
            request_context=record.request_context,
            matched_mock=record.matched_mock,
            scope=record.scope,
            response_status_code=record.response_status_code,
            created_at=record.created_at,
        )

        if record.id:
            document.id = PydanticObjectId(record.id)

        return document
