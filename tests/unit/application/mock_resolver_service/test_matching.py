import pytest

from app.application.services import MockResolverService
from tests.testkit.factories import MockFactory, RequestFactory
from tests.testkit.fakes import FakeMockRepository, FakeRequestLogRepository


class TestMatching:
    """Проверяет выбор подходящего мока."""

    @pytest.mark.asyncio
    async def test_resolve_returns_matching_candidate(
        self,
        mock_resolver_service: MockResolverService,
        fake_mock_repository: FakeMockRepository,
        fake_request_log_repository: FakeRequestLogRepository,
        request_factory: RequestFactory,
        mock_factory: MockFactory,
    ) -> None:
        """Проверяет, что подходящий кандидат возвращается и логируется."""
        mock = mock_factory.create_mock(
            mock_id="mock-1",
            name="users",
            path="/users",
            active=True,
            scope="user-a",
            response_status_code=200,
        )
        await fake_mock_repository.save(mock)
        request_context = request_factory.create_request_context(path="/users")

        result = await mock_resolver_service.resolve(request_context)

        assert result is not None
        assert result.mock.id == "mock-1"
        assert result.mock.name == "users"
        assert result.scope == "user-a"
        assert len(fake_request_log_repository.records) == 1
        assert fake_request_log_repository.records[0].matched_mock is not None
        assert fake_request_log_repository.records[0].matched_mock.id == "mock-1"
        assert fake_request_log_repository.records[0].response_status_code == 200

    @pytest.mark.asyncio
    async def test_resolve_selects_highest_priority_candidate(
        self,
        mock_resolver_service: MockResolverService,
        fake_mock_repository: FakeMockRepository,
        request_factory: RequestFactory,
        mock_factory: MockFactory,
    ) -> None:
        """Проверяет, что приоритет влияет на выбор кандидата."""
        mock_with_low_priority = mock_factory.create_mock(
            mock_id="low",
            name="low",
            path="/users",
            priority=1,
            active=True,
            scope="user-a",
        )
        mock_with_high_priority = mock_factory.create_mock(
            mock_id="high",
            name="high",
            path="/users",
            priority=10,
            active=True,
            scope="user-a",
        )
        await fake_mock_repository.save(mock_with_low_priority)
        await fake_mock_repository.save(mock_with_high_priority)

        request_context = request_factory.create_request_context(path="/users")

        result = await mock_resolver_service.resolve(request_context)

        assert result is not None
        assert result.mock.id == "high"
