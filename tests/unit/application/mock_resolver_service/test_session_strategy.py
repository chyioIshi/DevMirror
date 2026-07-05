from datetime import UTC, datetime

from app.application.mocks import MockSessionResolveStrategy
from app.application.request_logs import RequestLogService
from app.domain.shared import MatchOperator, MatchSource
from tests.testkit.factories import MockFactory, RequestFactory
from tests.testkit.fakes import FakeMockRepository, FakeRequestLogRepository


class TestMockSessionResolveStrategy:
    async def test_returns_none_when_session_header_is_missing(
        self,
        fake_mock_repository: FakeMockRepository,
        request_log_service: RequestLogService,
        request_factory: RequestFactory,
    ) -> None:
        strategy = MockSessionResolveStrategy(fake_mock_repository, request_log_service)

        result = await strategy.resolve(request_factory.create_request_context())

        assert result is None
        assert fake_mock_repository.find_latest_by_session_id_calls == []

    async def test_returns_none_when_session_header_is_empty(
        self,
        fake_mock_repository: FakeMockRepository,
        request_log_service: RequestLogService,
        request_factory: RequestFactory,
    ) -> None:
        strategy = MockSessionResolveStrategy(fake_mock_repository, request_log_service)

        result = await strategy.resolve(
            request_factory.create_request_context(headers={"mock-session-id": "  "})
        )

        assert result is None
        assert fake_mock_repository.find_latest_by_session_id_calls == []

    async def test_calls_repository_with_route_and_session_id(
        self,
        fake_mock_repository: FakeMockRepository,
        request_log_service: RequestLogService,
        request_factory: RequestFactory,
    ) -> None:
        strategy = MockSessionResolveStrategy(fake_mock_repository, request_log_service)

        result = await strategy.resolve(
            request_factory.create_request_context(
                method="POST",
                path="/users/42",
                headers={"mock-session-id": "test-run-123"},
            )
        )

        assert result is None
        assert fake_mock_repository.find_latest_by_session_id_calls == [
            ("POST", "/users/42", "test-run-123"),
        ]

    async def test_returns_found_mock(
        self,
        fake_mock_repository: FakeMockRepository,
        request_log_service: RequestLogService,
        request_factory: RequestFactory,
        mock_factory: MockFactory,
    ) -> None:
        mock = mock_factory.create_mock(
            mock_id="mock-1",
            path="/users/42",
            active=True,
            mock_session_id="test-run-123",
        )
        await fake_mock_repository.save(mock)
        strategy = MockSessionResolveStrategy(fake_mock_repository, request_log_service)

        result = await strategy.resolve(
            request_factory.create_request_context(
                path="/users/42",
                headers={"mock-session-id": "test-run-123"},
            )
        )

        assert result is not None
        assert result.mock.id == "mock-1"
        assert result.scope == "global"

    async def test_ignores_match_rules(
        self,
        fake_mock_repository: FakeMockRepository,
        fake_request_log_repository: FakeRequestLogRepository,
        request_log_service: RequestLogService,
        request_factory: RequestFactory,
        mock_factory: MockFactory,
    ) -> None:
        mock = mock_factory.create_mock(
            mock_id="mock-1",
            path="/users/42",
            active=True,
            mock_session_id="test-run-123",
            match_rules=[
                mock_factory.match_rule(
                    source=MatchSource.HEADER,
                    key="x-user",
                    operator=MatchOperator.EQ,
                    expected="admin",
                )
            ],
        )
        await fake_mock_repository.save(mock)
        strategy = MockSessionResolveStrategy(fake_mock_repository, request_log_service)

        result = await strategy.resolve(
            request_factory.create_request_context(
                path="/users/42",
                headers={"mock-session-id": "test-run-123", "x-user": "visitor"},
            )
        )

        assert result is not None
        assert result.mock.id == "mock-1"
        assert len(fake_request_log_repository.records) == 1
        assert fake_request_log_repository.records[0].matched_mock is not None

    async def test_picks_latest_mock(
        self,
        fake_mock_repository: FakeMockRepository,
        request_log_service: RequestLogService,
        request_factory: RequestFactory,
        mock_factory: MockFactory,
    ) -> None:
        older = mock_factory.create_mock(
            mock_id="000000000000000000000001",
            path="/users/42",
            active=True,
            priority=100,
            mock_session_id="test-run-123",
            updated_at=datetime(2026, 1, 1, tzinfo=UTC),
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        latest = mock_factory.create_mock(
            mock_id="000000000000000000000002",
            path="/users/42",
            active=True,
            priority=1,
            mock_session_id="test-run-123",
            updated_at=datetime(2026, 1, 2, tzinfo=UTC),
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        await fake_mock_repository.save(older)
        await fake_mock_repository.save(latest)
        strategy = MockSessionResolveStrategy(fake_mock_repository, request_log_service)

        result = await strategy.resolve(
            request_factory.create_request_context(
                path="/users/42",
                headers={"mock-session-id": "test-run-123"},
            )
        )

        assert result is not None
        assert result.mock.id == "000000000000000000000002"
