import httpx


class TestRouteValidation:
    """Проверяет валидацию API routes."""

    async def test_create_mock_returns_422_for_invalid_body(
        self,
        api_client: httpx.AsyncClient,
    ) -> None:
        """Проверяет 422 при некорректном body создания мока."""
        response = await api_client.post(
            "/admin/mocks",
            json={"name": "invalid", "path": "without-slash", "method": "GET"},
        )

        assert response.status_code == 422

    async def test_list_mocks_returns_422_for_invalid_query(
        self,
        api_client: httpx.AsyncClient,
    ) -> None:
        """Проверяет 422 при некорректном query списка моков."""
        response = await api_client.get("/admin/mocks", params={"method": "UNKNOWN"})

        assert response.status_code == 422

    async def test_update_mock_returns_422_for_active_field(
        self,
        api_client: httpx.AsyncClient,
    ) -> None:
        """Проверяет 422 при попытке обновить поле active."""
        response = await api_client.put("/admin/mocks/mock-1", json={"active": True})

        assert response.status_code == 422

    async def test_verify_request_logs_returns_422_for_invalid_body(
        self,
        api_client: httpx.AsyncClient,
    ) -> None:
        """Проверяет 422 при некорректном body проверки журнала."""
        response = await api_client.post(
            "/admin/request-logs/verify",
            json={"path": "/test", "method": "UNKNOWN"},
        )

        assert response.status_code == 422

    async def test_list_request_logs_returns_422_for_invalid_pagination(
        self,
        api_client: httpx.AsyncClient,
    ) -> None:
        """Проверяет 422 при некорректной пагинации журнала."""
        response = await api_client.request(
            "GET",
            "/admin/request-logs",
            json={"limit": 0},
        )

        assert response.status_code == 422
