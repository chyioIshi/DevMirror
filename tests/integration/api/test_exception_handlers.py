import httpx

from app.application.exceptions import (
    ApplicationError,
    ApplicationErrorCode,
    MockNotFoundError,
    OperationNotAllowedError,
    ResourceAlreadyExistsError,
    ValidationError,
)
from app.domain.mocks import InvalidScopeError, MockConflictError
from app.infra.exceptions import DatabaseConnectionError
from tests.testkit.fakes import FakeMockManagementService


class TestExceptionHandlers:
    """Проверяет API exception handlers."""

    async def test_mock_not_found_error_returns_404(
        self,
        api_client: httpx.AsyncClient,
        fake_mock_management_service: FakeMockManagementService,
    ) -> None:
        """Проверяет ответ handler для MockNotFoundError."""
        fake_mock_management_service.get_mock_error = MockNotFoundError(
            mock_id="missing",
        )

        response = await api_client.get("/admin/mocks/missing")

        assert response.status_code == 404
        assert response.json() == {
            "error": {
                "code": "MOCK_NOT_FOUND",
                "message": "Mock was not found",
                "details": {"mock_id": "missing"},
            },
        }

    async def test_validation_error_returns_422(
        self,
        api_client: httpx.AsyncClient,
        fake_mock_management_service: FakeMockManagementService,
    ) -> None:
        """Проверяет ответ handler для ValidationError."""
        fake_mock_management_service.update_mock_error = ValidationError(
            "Invalid update",
            details={"field": "name"},
        )

        response = await api_client.put("/admin/mocks/mock-1", json={"name": "new"})

        assert response.status_code == 422
        assert response.json() == {
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid update",
                "details": {"field": "name"},
            },
        }

    async def test_mock_conflict_error_returns_409(
        self,
        api_client: httpx.AsyncClient,
        fake_mock_management_service: FakeMockManagementService,
    ) -> None:
        """Проверяет ответ handler для MockConflictError."""
        fake_mock_management_service.activate_mock_error = MockConflictError(
            details={"mock_id": "mock-1"},
        )

        response = await api_client.post("/admin/mocks/mock-1/activate")

        assert response.status_code == 409
        assert response.json() == {
            "error": {
                "code": "MOCK_CONFLICT",
                "message": "Mock conflicts with an existing mock",
                "details": {"mock_id": "mock-1"},
            },
        }

    async def test_domain_error_returns_400(
        self,
        api_client: httpx.AsyncClient,
        fake_mock_management_service: FakeMockManagementService,
    ) -> None:
        """Проверяет ответ handler для DomainError."""
        fake_mock_management_service.create_mock_error = InvalidScopeError(
            details={"scope": ""},
        )

        response = await api_client.post(
            "/admin/mocks",
            json={
                "name": "new-mock",
                "path": "/new",
                "method": "GET",
                "response": {"status_code": 200},
            },
        )

        assert response.status_code == 400
        assert response.json() == {
            "error": {
                "code": "INVALID_SCOPE",
                "message": "Mock scope is invalid",
                "details": {"scope": ""},
            },
        }

    async def test_resource_already_exists_error_returns_409(
        self,
        api_client: httpx.AsyncClient,
        fake_mock_management_service: FakeMockManagementService,
    ) -> None:
        """Проверяет ответ handler для ResourceAlreadyExistsError."""
        fake_mock_management_service.create_mock_error = ResourceAlreadyExistsError(
            details={"name": "new-mock"},
        )

        response = await api_client.post(
            "/admin/mocks",
            json={
                "name": "new-mock",
                "path": "/new",
                "method": "GET",
                "response": {"status_code": 200},
            },
        )

        assert response.status_code == 409
        assert response.json()["error"]["code"] == "RESOURCE_ALREADY_EXISTS"

    async def test_operation_not_allowed_error_returns_400(
        self,
        api_client: httpx.AsyncClient,
        fake_mock_management_service: FakeMockManagementService,
    ) -> None:
        """Проверяет ответ handler для OperationNotAllowedError без конфликта."""
        fake_mock_management_service.deactivate_mock_error = OperationNotAllowedError(
            details={"mock_id": "mock-1"},
        )

        response = await api_client.post("/admin/mocks/mock-1/deactivate")

        assert response.status_code == 400
        assert response.json()["error"]["code"] == "OPERATION_NOT_ALLOWED"

    async def test_operation_not_allowed_conflict_returns_409(
        self,
        api_client: httpx.AsyncClient,
        fake_mock_management_service: FakeMockManagementService,
    ) -> None:
        """Проверяет ответ handler для конфликтного OperationNotAllowedError."""
        fake_mock_management_service.deactivate_mock_error = OperationNotAllowedError(
            details={"mock_id": "mock-1"},
            conflict=True,
        )

        response = await api_client.post("/admin/mocks/mock-1/deactivate")

        assert response.status_code == 409
        assert response.json()["error"]["code"] == "OPERATION_NOT_ALLOWED"

    async def test_generic_application_error_returns_400(
        self,
        api_client: httpx.AsyncClient,
        fake_mock_management_service: FakeMockManagementService,
    ) -> None:
        """Проверяет ответ handler для базового ApplicationError."""
        fake_mock_management_service.delete_mock_error = ApplicationError(
            code=ApplicationErrorCode.VALIDATION_ERROR,
            message="Application failed",
        )

        response = await api_client.delete("/admin/mocks/mock-1")

        assert response.status_code == 400
        assert response.json()["error"]["message"] == "Application failed"

    async def test_infrastructure_error_returns_500(
        self,
        api_client: httpx.AsyncClient,
        fake_mock_management_service: FakeMockManagementService,
    ) -> None:
        """Проверяет ответ handler для InfrastructureError."""
        fake_mock_management_service.list_mocks_error = DatabaseConnectionError(
            details={"operation": "list_mocks"},
        )

        response = await api_client.get("/admin/mocks")

        assert response.status_code == 500
        assert response.json() == {
            "error": {
                "code": "DATABASE_CONNECTION_ERROR",
                "message": "Database connection failed",
                "details": {"operation": "list_mocks"},
            },
        }

    async def test_unknown_error_returns_500(
        self,
        api_client_no_raise: httpx.AsyncClient,
        fake_mock_management_service: FakeMockManagementService,
    ) -> None:
        """Проверяет ответ handler для неизвестного исключения."""
        fake_mock_management_service.get_mock_error = RuntimeError("boom")

        response = await api_client_no_raise.get("/admin/mocks/mock-1")

        assert response.status_code == 500
        assert response.json() == {
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Internal server error",
                "details": {},
            },
        }
