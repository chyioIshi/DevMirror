from app.api.mappers.request_log_record_contract_mapper import (
    RequestLogRecordContractMapper,
)
from app.domain.request_logs.models import MatchedMock, RequestLogRecord
from app.domain.shared import HttpMethod


class TestRequestLogRecordContractMapper:
    """Проверяет маппинг request log domain model в API dto и обратно."""

    def test_from_domain_maps_record_with_matched_mock(self, request_factory) -> None:
        """Проверяет маппинг записи журнала с найденным мокам."""
        record = RequestLogRecord(
            id="record-1",
            request_context=request_factory.create_request_context(
                path="/users",
                headers={"user": "user1"},
                query_string="page=1",
                body={"request": True},
            ),
            matched_mock=MatchedMock(
                id="mock-1",
                name="users",
                path="/users",
                method=HttpMethod.GET,
                scope="user",
                response_status_code=200,
                response_body={"ok": True},
            ),
            scope="user",
            response_status_code=200,
        )

        item = RequestLogRecordContractMapper.from_domain_request_log_record_model(
            record,
        )

        assert item.id == "record-1"
        assert item.request_context.path == "/users"
        assert item.request_context.headers == {"user": "user1"}
        assert item.request_context.query_params == {"page": "1"}
        assert item.request_context.body == {"request": True}
        assert item.matched_mock is not None
        assert item.matched_mock.id == "mock-1"
        assert item.scope == "user"
        assert item.response_status_code == 200

    def test_from_domain_uses_empty_id_when_record_has_no_id(self, request_factory) -> None:
        """Проверяет fallback id для несохраненной записи."""
        record = RequestLogRecord(
            request_context=request_factory.create_request_context(path="/users"),
        )

        item = RequestLogRecordContractMapper.from_domain_request_log_record_model(
            record,
        )

        assert item.id == ""
        assert item.matched_mock is None

