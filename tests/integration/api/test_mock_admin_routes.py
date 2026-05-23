import httpx

from app.domain.shared import HttpMethod
from tests.testkit.fakes import FakeMockManagementService


class TestMockAdminRoutes:
    """Проверяет mock admin API routes."""

    async def test_create_mock_calls_service_and_returns_created_mock(
        self,
        api_client: httpx.AsyncClient,
        fake_mock_management_service: FakeMockManagementService,
    ) -> None:
        """Проверяет создание мока через API."""
        response = await api_client.post(
            "/admin/mocks",
            json={
                "name": "new-mock",
                "path": "/new",
                "method": "GET",
                "response": {"status_code": 200},
            },
        )

        assert response.status_code == 201
        assert response.json()["id"] == "000000000000000000000001"
        assert response.json()["name"] == "created-mock"
        assert len(fake_mock_management_service.create_mock_calls) == 1
        assert fake_mock_management_service.create_mock_calls[0].active is False

    async def test_get_mock_returns_found_mock(
        self,
        api_client: httpx.AsyncClient,
        fake_mock_management_service: FakeMockManagementService,
    ) -> None:
        """Проверяет получение мока по id."""
        response = await api_client.get("/admin/mocks/mock-1")

        assert response.status_code == 200
        assert response.json()["id"] == "000000000000000000000002"
        assert response.json()["name"] == "fetched-mock"
        assert fake_mock_management_service.get_mock_calls == ["mock-1"]

    async def test_list_mocks_passes_filters_and_pagination(
        self,
        api_client: httpx.AsyncClient,
        fake_mock_management_service: FakeMockManagementService,
    ) -> None:
        """Проверяет список моков с фильтрами и пагинацией."""
        response = await api_client.request(
            "GET",
            "/admin/mocks",
            params={
                "path": "/created",
                "method": "GET",
                "active": "false",
                "scope": "global",
            },
            json={"limit": 10, "offset": 5},
        )

        assert response.status_code == 200
        assert response.json()["total"] == 2
        filters, limit, offset = fake_mock_management_service.list_mocks_calls[0]
        assert filters.path == "/created"
        assert filters.method == HttpMethod.GET
        assert filters.active is False
        assert filters.scope == "global"
        assert limit == 10
        assert offset == 5

    async def test_update_mock_passes_update_command(
        self,
        api_client: httpx.AsyncClient,
        fake_mock_management_service: FakeMockManagementService,
    ) -> None:
        """Проверяет обновление мока через API."""
        response = await api_client.put(
            "/admin/mocks/mock-1",
            json={"name": "updated-name"},
        )

        assert response.status_code == 200
        assert response.json()["id"] == "000000000000000000000003"
        command = fake_mock_management_service.update_mock_calls[0]
        assert command.mock_id == "mock-1"
        assert command.name == "updated-name"

    async def test_delete_mock_calls_service(
        self,
        api_client: httpx.AsyncClient,
        fake_mock_management_service: FakeMockManagementService,
    ) -> None:
        """Проверяет удаление мока через API."""
        response = await api_client.delete("/admin/mocks/mock-1")

        assert response.status_code == 200
        assert fake_mock_management_service.delete_mock_calls == ["mock-1"]

    async def test_activate_mock_passes_deactivate_conflicting(
        self,
        api_client: httpx.AsyncClient,
        fake_mock_management_service: FakeMockManagementService,
    ) -> None:
        """Проверяет активацию мока через API."""
        response = await api_client.post(
            "/admin/mocks/mock-1/activate",
            params={"deactivate_conflicting": "true"},
        )

        assert response.status_code == 200
        assert response.json()["active"] is True
        assert fake_mock_management_service.activate_mock_calls == [("mock-1", True)]

    async def test_deactivate_mock_calls_service(
        self,
        api_client: httpx.AsyncClient,
        fake_mock_management_service: FakeMockManagementService,
    ) -> None:
        """Проверяет деактивацию мока через API."""
        response = await api_client.post("/admin/mocks/mock-1/deactivate")

        assert response.status_code == 200
        assert response.json()["active"] is False
        assert fake_mock_management_service.deactivate_mock_calls == ["mock-1"]

