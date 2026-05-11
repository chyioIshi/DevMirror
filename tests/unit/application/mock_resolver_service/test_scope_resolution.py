import pytest

from app.application.services import MockResolverService
from app.domain.shared import HttpMethod
from tests.testkit.factories import RequestFactory
from tests.testkit.fakes import FakeMockRepository, FakeScopeResolver


class TestScopeResolution:
    """Проверяет передачу scope при поиске кандидатов."""

    @pytest.mark.asyncio
    async def test_resolve_searches_requested_scope_and_default_scope(
        self,
        mock_resolver_service: MockResolverService,
        fake_mock_repository: FakeMockRepository,
        fake_scope_resolver: FakeScopeResolver,
        request_factory: RequestFactory,
    ) -> None:
        """Проверяет, что user scope дополняется global scope."""
        fake_scope_resolver.scope = "user-a"
        request_context = request_factory.create_request_context(path="/users")

        await mock_resolver_service.resolve(request_context)

        assert fake_mock_repository.list_candidates_calls == [
            (HttpMethod.GET, "/users", ("user-a", "global")),
        ]

    @pytest.mark.asyncio
    async def test_resolve_searches_default_scope_once(
        self,
        mock_resolver_service: MockResolverService,
        fake_mock_repository: FakeMockRepository,
        fake_scope_resolver: FakeScopeResolver,
        request_factory: RequestFactory,
    ) -> None:
        """Проверяет, что global scope не дублируется."""
        fake_scope_resolver.scope = "global"
        request_context = request_factory.create_request_context(path="/users")

        await mock_resolver_service.resolve(request_context)

        assert fake_mock_repository.list_candidates_calls == [
            (HttpMethod.GET, "/users", ("global",)),
        ]
