import httpx

from app.domain.shared import HttpMethod
from tests.testkit.fakes import FakeRequestLogService


class TestRequestLogRoutes:
    """Проверяет request log API routes."""

    async def test_list_request_logs_passes_pagination(
        self,
        api_client: httpx.AsyncClient,
        fake_request_log_service: FakeRequestLogService,
    ) -> None:
        """Проверяет получение журнала запросов."""
        response = await api_client.request(
            "GET",
            "/admin/request-logs",
            json={"limit": 10, "offset": 5},
        )

        assert response.status_code == 200
        assert response.json()["total"] == 1
        assert fake_request_log_service.list_records_calls == [(10, 5)]

    async def test_verify_request_logs_passes_expectation(
        self,
        api_client: httpx.AsyncClient,
        fake_request_log_service: FakeRequestLogService,
    ) -> None:
        """Проверяет роут verify: проверку того,
         что передаваемый в теле запрос к сервису был."""
        response = await api_client.post(
            "/admin/request-logs/verify",
            json={
                "path": "/created",
                "method": "GET",
                "expected_count": 1,
                "matched_mock_id": "mock-1",
            },
        )

        assert response.status_code == 200
        assert response.json() == {"matched": True, "actual_count": 1}
        expectation = fake_request_log_service.verify_calls[0]
        assert expectation.path == "/created"
        assert expectation.method == HttpMethod.GET
        assert expectation.expected_count == 1
        assert expectation.matched_mock_id == "mock-1"

    async def test_clear_request_logs_calls_service(
        self,
        api_client: httpx.AsyncClient,
        fake_request_log_service: FakeRequestLogService,
    ) -> None:
        """Проверяет очистку журнала запросов."""
        response = await api_client.delete("/admin/request-logs")

        assert response.status_code == 200
        assert fake_request_log_service.clear_calls == 1
