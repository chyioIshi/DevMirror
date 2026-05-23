from beanie import PydanticObjectId

from app.domain.request_contexts import RequestContext
from app.domain.request_logs.models import MatchedMock, RequestLogRecord
from app.infra.db.mongo.documents import (
    MatchedMockDocument,
    RequestContextDocument,
    RequestLogDocument,
)


class RequestLogMapper:
    """Преобразует request logs между Mongo-документами и доменными моделями."""

    @staticmethod
    def to_domain(document: RequestLogDocument) -> RequestLogRecord:
        """Преобразует сохранённый Mongo-документ в доменную модель."""
        return RequestLogRecord(
            id=str(document.id),
            request_context=RequestContext(
                id=document.request_context.id,
                method=document.request_context.method,
                path=document.request_context.path,
                headers=document.request_context.headers,
                query_params=document.request_context.query_params,
                body=document.request_context.body,
                timestamp=document.request_context.timestamp,
            ),
            matched_mock=(
                MatchedMock(
                    id=document.matched_mock.id,
                    name=document.matched_mock.name,
                    path=document.matched_mock.path,
                    method=document.matched_mock.method,
                    scope=document.matched_mock.scope,
                    response_status_code=document.matched_mock.response_status_code,
                    response_body=document.matched_mock.response_body,
                )
                if document.matched_mock is not None
                else None
            ),
            scope=document.scope,
            response_status_code=document.response_status_code,
            created_at=document.created_at,
        )

    @staticmethod
    def to_document(record: RequestLogRecord) -> RequestLogDocument:
        """Преобразует доменную модель в Mongo-документ."""
        document = RequestLogDocument(
            request_context=RequestContextDocument(
                id=record.request_context.id,
                method=record.request_context.method,
                path=record.request_context.path,
                headers=record.request_context.headers,
                query_params=record.request_context.query_params,
                body=record.request_context.body,
                timestamp=record.request_context.timestamp,
            ),
            matched_mock=(
                MatchedMockDocument(
                    id=record.matched_mock.id,
                    name=record.matched_mock.name,
                    path=record.matched_mock.path,
                    method=record.matched_mock.method,
                    scope=record.matched_mock.scope,
                    response_status_code=record.matched_mock.response_status_code,
                    response_body=record.matched_mock.response_body,
                )
                if record.matched_mock is not None
                else None
            ),
            scope=record.scope,
            response_status_code=record.response_status_code,
            created_at=record.created_at,
        )

        if record.id:
            document.id = PydanticObjectId(record.id)

        return document
