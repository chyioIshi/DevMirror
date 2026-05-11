import pytest

from app.application.services import MockResolverService
from app.domain.shared import MatchOperator, MatchSource
from tests.testkit.factories import MockFactory, RequestFactory
from tests.testkit.fakes import FakeMockRepository, FakeRequestLogRepository


class TestNoMatch:
    """Проверяет сценарии без найденного мока."""

    @pytest.mark.asyncio
    async def test_resolve_returns_none_when_repository_has_no_candidates(
        self,
        mock_resolver_service: MockResolverService,
        fake_request_log_repository: FakeRequestLogRepository,
        request_factory: RequestFactory,
    ) -> None:
        """Проверяет, что отсутствие моков-кандидатов возвращает None."""
        request_context = request_factory.create_request_context(path="/missing")

        result = await mock_resolver_service.resolve(request_context)

        assert result is None
        assert len(fake_request_log_repository.records) == 1
        assert fake_request_log_repository.records[0].matched_mock is None
        assert fake_request_log_repository.records[0].response_status_code is None

    @pytest.mark.asyncio
    async def test_resolve_returns_none_when_candidate_rules_do_not_match(
        self,
        mock_resolver_service: MockResolverService,
        fake_mock_repository: FakeMockRepository,
        fake_request_log_repository: FakeRequestLogRepository,
        request_factory: RequestFactory,
        mock_factory: MockFactory,
    ) -> None:
        """Проверяет, что неподходящие правила исключают кандидата."""

        mock = mock_factory.create_mock(
            mock_id="mock-1",
            path="/users",
            active=True,
            scope="user-a",
            match_rules=[
                mock_factory.match_rule(
                    source=MatchSource.HEADER,
                    key="x-user",
                    operator=MatchOperator.EQ,
                    expected="admin",
                ),
            ],
        )

        await fake_mock_repository.save(mock)

        request_context = request_factory.create_request_context(
            path="/users",
            headers={"x-user": "visitor"},
        )

        result = await mock_resolver_service.resolve(request_context)

        assert result is None
        assert len(fake_request_log_repository.records) == 1
        assert fake_request_log_repository.records[0].matched_mock is None
