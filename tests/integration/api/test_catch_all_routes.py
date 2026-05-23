import httpx

from tests.testkit.fakes import FakeMockResolverService, FakeRequestContextResolver


class TestCatchAllRoutes:
    """Проверяет catch-all API route."""

    async def test_returns_resolved_mock_response(
        self,
        api_client: httpx.AsyncClient,
        fake_mock_resolver_service: FakeMockResolverService,
        fake_request_context_resolver: FakeRequestContextResolver,
    ) -> None:
        """Проверяет, что catch-all возвращает найденный mock response."""
        response = await api_client.get("/external")

        assert response.status_code == 202
        assert response.json() == {"message": "matched"}
        assert len(fake_request_context_resolver.resolve_calls) == 1
        assert fake_mock_resolver_service.resolve_calls == [
            fake_request_context_resolver.request_context
        ]

    async def test_returns_404_when_mock_is_not_resolved(
        self,
        api_client: httpx.AsyncClient,
        fake_mock_resolver_service: FakeMockResolverService,
    ) -> None:
        """Проверяет 404, если активный мок не найден."""
        fake_mock_resolver_service.resolved_mock = None

        response = await api_client.get("/unknown")

        assert response.status_code == 404
        assert response.json() == {"detail": "No active mock matched the request"}

    async def test_does_not_handle_reserved_paths(
        self,
        api_client: httpx.AsyncClient,
        fake_request_context_resolver: FakeRequestContextResolver,
    ) -> None:
        """Проверяет, что служебные пути не обрабатываются catch-all."""
        response = await api_client.get("/favicon.ico")

        assert response.status_code == 404
        assert response.json() == {"detail": "Not this route!!!"}
        assert fake_request_context_resolver.resolve_calls == []
