import pytest

from app.application.request_logs import RequestLogService
from app.domain.mocks.models.resolution import ResolvedMock, RuleMatchResult
from app.domain.shared import HttpMethod
from tests.testkit.factories import MockFactory, RequestFactory
from tests.testkit.fakes import FakeRequestLogRepository


class TestCreateRecord:
    """Проверяет создание записей журнала запросов."""

    @pytest.mark.asyncio
    async def test_create_record_without_match_stores_unmatched_request(
        self,
        request_log_service: RequestLogService,
        fake_request_log_repository: FakeRequestLogRepository,
        request_factory: RequestFactory,
    ) -> None:
        """Проверяет, что запрос без мока сохраняется без matched_mock."""
        request_context = request_factory.create_request_context(path="/users")

        await request_log_service.create_record(
            request_context=request_context,
            scope="user-a",
            resolved_mock=None,
        )

        record = fake_request_log_repository.records[0]
        assert record.request_context == request_context
        assert record.scope == "user-a"
        assert record.matched_mock is None
        assert record.response_status_code is None

    @pytest.mark.asyncio
    async def test_create_record_with_match_stores_matched_mock_snapshot(
        self,
        request_log_service: RequestLogService,
        fake_request_log_repository: FakeRequestLogRepository,
        request_factory: RequestFactory,
        mock_factory: MockFactory,
    ) -> None:
        """Проверяет, что найденный мок сохраняется как snapshot."""
        request_context = request_factory.create_request_context(path="/users")
        mock = mock_factory.create_mock(
            mock_id="mock-1",
            name="users",
            path="/users",
            method=HttpMethod.GET,
            scope="user-a",
            response_status_code=201,
            response_body={"created": True},
        )
        resolved_mock = ResolvedMock(
            mock=mock,
            scope="user-a",
            rule_result=RuleMatchResult(matched=True),
        )

        await request_log_service.create_record(
            request_context=request_context,
            scope="user-a",
            resolved_mock=resolved_mock,
        )

        record = fake_request_log_repository.records[0]
        assert record.response_status_code == 201
        assert record.matched_mock is not None
        assert record.matched_mock.id == "mock-1"
        assert record.matched_mock.name == "users"
        assert record.matched_mock.path == "/users"
        assert record.matched_mock.scope == "user-a"
        assert record.matched_mock.response_status_code == 201
        assert record.matched_mock.response_body == {"created": True}
