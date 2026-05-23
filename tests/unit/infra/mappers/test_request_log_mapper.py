from datetime import UTC, datetime

from beanie import PydanticObjectId

from app.domain.request_logs.models import MatchedMock, RequestLogRecord
from app.domain.shared import HttpMethod
from app.infra.db.mongo.documents import (
    MatchedMockDocument,
    RequestContextDocument,
    RequestLogDocument,
)
from app.infra.mappers.request_log_mapper import RequestLogMapper


class TestRequestLogMapper:
    """Проверяет преобразование request log между domain и Mongo document."""

    def test_to_document_maps_record_with_matched_mock(
        self,
        request_factory,
        beanie_document_constructors: None,
    ) -> None:
        """Проверяет маппинг записи журнала в Mongo document."""
        created_at = datetime(2026, 1, 1, tzinfo=UTC)
        record = RequestLogRecord(
            id="000000000000000000000010",
            request_context=request_factory.create_request_context(
                path="/users",
                headers={"x-user": "alice"},
                query_string="page=1",
                body={"request": True},
            ),
            matched_mock=MatchedMock(
                id="mock-1",
                name="users",
                path="/users",
                method=HttpMethod.GET,
                scope="user_name",
                response_status_code=200,
                response_body={"ok": True},
            ),
            scope="user_name",
            response_status_code=200,
            created_at=created_at,
        )

        document = RequestLogMapper.to_document(record)

        assert document.id == PydanticObjectId("000000000000000000000010")
        assert document.request_context.path == "/users"
        assert document.request_context.headers == {"x-user": "alice"}
        assert document.request_context.query_params == {"page": "1"}
        assert document.request_context.body == {"request": True}
        assert document.matched_mock is not None
        assert document.matched_mock.id == "mock-1"
        assert document.scope == "user_name"
        assert document.response_status_code == 200
        assert document.created_at == created_at

    def test_to_domain_maps_document_without_matched_mock(
        self,
        beanie_document_constructors: None,
    ) -> None:
        """Проверяет маппинг Mongo document без найденного мока."""
        created_at = datetime(2026, 1, 1, tzinfo=UTC)
        timestamp = datetime(2026, 1, 1, 12, tzinfo=UTC)
        document = RequestLogDocument(
            request_context=RequestContextDocument(
                id="request-1",
                method=HttpMethod.POST,
                path="/users",
                headers={"x-user": "alice"},
                query_params={"page": "1"},
                body={"request": True},
                timestamp=timestamp,
            ),
            matched_mock=None,
            scope="user_name",
            response_status_code=None,
            created_at=created_at,
        )
        document.id = PydanticObjectId("000000000000000000000011")

        record = RequestLogMapper.to_domain(document)

        assert record.id == "000000000000000000000011"
        assert record.request_context.id == "request-1"
        assert record.request_context.method == HttpMethod.POST
        assert record.request_context.path == "/users"
        assert record.request_context.headers == {"x-user": "alice"}
        assert record.request_context.query_params == {"page": "1"}
        assert record.request_context.body == {"request": True}
        assert record.request_context.timestamp == timestamp
        assert record.matched_mock is None
        assert record.scope == "user_name"
        assert record.response_status_code is None
        assert record.created_at == created_at

    def test_to_domain_maps_document_with_matched_mock(
        self,
        beanie_document_constructors: None,
    ) -> None:
        """Проверяет маппинг Mongo document с найденным мокам."""
        document = RequestLogDocument(
            request_context=RequestContextDocument(
                id="request-1",
                method=HttpMethod.GET,
                path="/users",
            ),
            matched_mock=MatchedMockDocument(
                id="mock-1",
                name="users",
                path="/users",
                method=HttpMethod.GET,
                scope="user_name",
                response_status_code=200,
                response_body={"ok": True},
            ),
        )

        record = RequestLogMapper.to_domain(document)

        assert record.matched_mock is not None
        assert record.matched_mock.id == "mock-1"
        assert record.matched_mock.response_body == {"ok": True}
