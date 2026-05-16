from app.domain.request_logs.models import (
    MatchedMock,
    RequestLogRecord,
    RequestLogVerificationExpectation,
)
from app.domain.shared import HttpMethod


class TestRequestLogRecord:
    """Проверяет RecordLog журнала запросов."""

    def test_matches_expectation_by_method_and_path(self, request_factory) -> None:
        """Проверяет совпадение по методу и path."""
        record = RequestLogRecord(
            request_context=request_factory.create_request_context(path="/users"),
        )

        assert record.matches_expectation(
            RequestLogVerificationExpectation(
                path="/users",
                method=HttpMethod.GET,
            ),
        )

    def test_does_not_match_different_path(self, request_factory) -> None:
        """Проверяет несовпадение по path."""
        record = RequestLogRecord(
            request_context=request_factory.create_request_context(path="/users"),
        )

        assert not record.matches_expectation(
            RequestLogVerificationExpectation(
                path="/orders",
                method=HttpMethod.GET,
            ),
        )

    def test_matches_expectation_by_matched_mock_id(self, request_factory) -> None:
        """Проверяет совпадение по id найденного мока."""
        record = RequestLogRecord(
            request_context=request_factory.create_request_context(path="/users"),
            matched_mock=MatchedMock(
                id="mock-1",
                name="users",
                path="/users",
                method=HttpMethod.GET,
                scope="global",
                response_status_code=200,
            ),
        )

        assert record.matches_expectation(
            RequestLogVerificationExpectation(
                path="/users",
                method=HttpMethod.GET,
                matched_mock_id="mock-1",
            ),
        )
