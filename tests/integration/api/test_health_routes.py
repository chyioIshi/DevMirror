import httpx


class TestHealthRoutes:
    """Проверяет health API routes."""

    async def test_healthcheck_returns_ok(self, api_client: httpx.AsyncClient) -> None:
        """Проверяет успешный healthcheck."""
        response = await api_client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

