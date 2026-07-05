import pytest

from app.application.exceptions import MockNotFoundError
from app.application.mocks import MockResolverService
from app.domain.mocks.models.resolution import ResolvedMock, RuleMatchResult
from app.domain.request_contexts import RequestContext
from tests.testkit.factories import MockFactory, RequestFactory


class FakeResolveStrategy:
    def __init__(self, resolved_mock: ResolvedMock | None) -> None:
        self.resolved_mock = resolved_mock
        self.resolve_calls: list[RequestContext] = []

    async def resolve(self, request_context: RequestContext) -> ResolvedMock | None:
        self.resolve_calls.append(request_context)
        return self.resolved_mock


class TestResolverOrder:
    async def test_session_strategy_wins_over_default_strategy(
        self,
        request_factory: RequestFactory,
        mock_factory: MockFactory,
    ) -> None:
        request_context = request_factory.create_request_context(path="/users/42")
        session_resolved = self._resolved_mock(mock_factory, "session")
        default_resolved = self._resolved_mock(mock_factory, "default")
        session_strategy = FakeResolveStrategy(session_resolved)
        default_strategy = FakeResolveStrategy(default_resolved)
        resolver = MockResolverService(
            strategies=[
                session_strategy,
                default_strategy,
            ]
        )

        result = await resolver.resolve(request_context)

        assert result.mock.id == "session"
        assert session_strategy.resolve_calls == [request_context]
        assert default_strategy.resolve_calls == []

    async def test_default_strategy_is_used_when_session_strategy_returns_none(
        self,
        request_factory: RequestFactory,
        mock_factory: MockFactory,
    ) -> None:
        request_context = request_factory.create_request_context(path="/users/42")
        default_resolved = self._resolved_mock(mock_factory, "default")
        session_strategy = FakeResolveStrategy(None)
        default_strategy = FakeResolveStrategy(default_resolved)
        resolver = MockResolverService(
            strategies=[
                session_strategy,
                default_strategy,
            ]
        )

        result = await resolver.resolve(request_context)

        assert result.mock.id == "default"
        assert session_strategy.resolve_calls == [request_context]
        assert default_strategy.resolve_calls == [request_context]

    async def test_raises_mock_not_found_when_no_strategy_resolves(
        self,
        request_factory: RequestFactory,
    ) -> None:
        request_context = request_factory.create_request_context(path="/missing")
        resolver = MockResolverService(
            strategies=[
                FakeResolveStrategy(None),
                FakeResolveStrategy(None),
            ]
        )

        with pytest.raises(MockNotFoundError) as error:
            await resolver.resolve(request_context)

        assert error.value.code == "MOCK_NOT_FOUND"
        assert error.value.message == "No active mock matched the request"

    def _resolved_mock(self, mock_factory: MockFactory, mock_id: str) -> ResolvedMock:
        return ResolvedMock(
            mock=mock_factory.create_mock(mock_id=mock_id, active=True),
            scope="global",
            rule_result=RuleMatchResult(matched=True, score=1),
        )
