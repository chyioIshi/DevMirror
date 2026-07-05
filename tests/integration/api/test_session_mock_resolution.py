from collections.abc import AsyncIterator

import httpx
import pytest
from fastapi import FastAPI

from app.api.error_handlers import register_exception_handlers
from app.api.routes import catch_all_router, mock_admin_router
from app.application.mocks import (
    MockManagementService,
    MockResolverService,
    MockSessionResolveStrategy,
    RuleMatchingResolveStrategy,
)
from app.application.request_logs import RequestLogService
from app.config import AppSettings
from app.di import (
    get_app_settings,
    get_mock_management_service,
    get_mock_resolver_service,
    get_mock_response_builder,
    get_request_context_resolver,
    get_side_effect_execution_service,
)
from app.domain.mocks.policies import MockActivationPolicy, MockSelectionPolicy
from app.domain.mocks.services import (
    MockConflictService,
    MockResolutionService,
    RuleMatcherService,
)
from app.infra.context import RequestContextResolver
from app.infra.request import RequestDataReader
from app.infra.response import MockResponseBuilder
from tests.testkit.fakes import (
    FakeMockRepository,
    FakeRequestLogRepository,
    FakeSideEffectExecutionService,
)


@pytest.fixture
def session_api_repository() -> FakeMockRepository:
    return FakeMockRepository()


@pytest.fixture
def session_api_app(session_api_repository: FakeMockRepository) -> FastAPI:
    settings = AppSettings(
        admin_prefix="/admin/mocks",
        request_log_prefix="/admin/request-logs",
        health_prefix="/health",
    )
    request_log_service = RequestLogService(FakeRequestLogRepository())
    mock_management_service = MockManagementService(
        repository=session_api_repository,
        conflict_service=MockConflictService(),
        activation_policy=MockActivationPolicy(),
    )
    mock_resolution_service = MockResolutionService(
        rule_matcher=RuleMatcherService(),
        selection_policy=MockSelectionPolicy(),
    )
    mock_resolver_service = MockResolverService(
        strategies=[
            MockSessionResolveStrategy(
                mock_repository=session_api_repository,
                request_log_service=request_log_service,
            ),
            RuleMatchingResolveStrategy(
                mock_repository=session_api_repository,
                request_log_service=request_log_service,
                scope_resolver=settings_scope_resolver(settings),
                mock_resolution_service=mock_resolution_service,
                default_scope=settings.default_scope,
            ),
        ],
    )

    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(mock_admin_router, prefix="/admin/mocks")
    app.include_router(catch_all_router)
    app.dependency_overrides[get_app_settings] = lambda: settings
    app.dependency_overrides[get_mock_management_service] = lambda: mock_management_service
    app.dependency_overrides[get_mock_resolver_service] = lambda: mock_resolver_service
    app.dependency_overrides[get_side_effect_execution_service] = lambda: (
        FakeSideEffectExecutionService()
    )
    app.dependency_overrides[get_request_context_resolver] = lambda: RequestContextResolver(
        request_data_accessor=RequestDataReader(),
    )
    app.dependency_overrides[get_mock_response_builder] = lambda: MockResponseBuilder()
    return app


@pytest.fixture
async def session_api_client(session_api_app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=session_api_app),
        base_url="http://test",
    ) as client:
        yield client


class TestSessionMockResolution:
    async def test_create_mock_accepts_mock_session_id(
        self,
        session_api_client: httpx.AsyncClient,
    ) -> None:
        response = await session_api_client.post(
            "/admin/mocks",
            json=self._mock_payload(
                name="test session mock",
                path="/users/42",
                mock_session_id="test-run-123",
                body={"source": "session"},
            ),
        )

        assert response.status_code == 201
        assert response.json()["mock_session_id"] == "test-run-123"

    async def test_runtime_request_with_matching_header_returns_session_mock(
        self,
        session_api_client: httpx.AsyncClient,
    ) -> None:
        await self._create_and_activate_default_mock(session_api_client)
        await self._create_and_activate_session_mock(session_api_client)

        response = await session_api_client.get(
            "/users/42",
            headers={"mock-session-id": "test-run-123"},
        )

        assert response.status_code == 200
        assert response.json() == {"source": "session"}

    async def test_runtime_request_without_header_falls_back_to_default_resolver(
        self,
        session_api_client: httpx.AsyncClient,
    ) -> None:
        await self._create_and_activate_default_mock(session_api_client)
        await self._create_and_activate_session_mock(session_api_client)

        response = await session_api_client.get("/users/42")

        assert response.status_code == 200
        assert response.json() == {"source": "default"}

    async def test_unknown_session_id_falls_back_to_default_resolver(
        self,
        session_api_client: httpx.AsyncClient,
    ) -> None:
        await self._create_and_activate_default_mock(session_api_client)
        await self._create_and_activate_session_mock(session_api_client)

        response = await session_api_client.get(
            "/users/42",
            headers={"mock-session-id": "unknown"},
        )

        assert response.status_code == 200
        assert response.json() == {"source": "default"}

    async def test_inactive_session_mock_is_ignored(
        self,
        session_api_client: httpx.AsyncClient,
    ) -> None:
        await self._create_and_activate_default_mock(session_api_client)
        await self._create_session_mock(session_api_client)

        response = await session_api_client.get(
            "/users/42",
            headers={"mock-session-id": "test-run-123"},
        )

        assert response.status_code == 200
        assert response.json() == {"source": "default"}

    async def _create_and_activate_default_mock(self, client: httpx.AsyncClient) -> str:
        response = await client.post(
            "/admin/mocks",
            json=self._mock_payload(
                name="default mock",
                path="/users/42",
                body={"source": "default"},
            ),
        )
        mock_id = response.json()["id"]
        await client.post(f"/admin/mocks/{mock_id}/activate")
        return mock_id

    async def _create_and_activate_session_mock(self, client: httpx.AsyncClient) -> str:
        mock_id = await self._create_session_mock(client)
        await client.post(f"/admin/mocks/{mock_id}/activate")
        return mock_id

    async def _create_session_mock(self, client: httpx.AsyncClient) -> str:
        response = await client.post(
            "/admin/mocks",
            json=self._mock_payload(
                name="session mock",
                path="/users/42",
                mock_session_id="test-run-123",
                body={"source": "session"},
                match_rules=[
                    {
                        "source": "header",
                        "key": "x-never",
                        "operator": "eq",
                        "expected": "match",
                    }
                ],
            ),
        )
        return response.json()["id"]

    def _mock_payload(
        self,
        *,
        name: str,
        path: str,
        body: dict[str, str],
        mock_session_id: str | None = None,
        match_rules: list[dict[str, str]] | None = None,
    ) -> dict[str, object]:
        payload: dict[str, object] = {
            "name": name,
            "method": "GET",
            "path": path,
            "response": {
                "status_code": 200,
                "body": body,
            },
        }
        if mock_session_id is not None:
            payload["mock_session_id"] = mock_session_id
        if match_rules is not None:
            payload["match_rules"] = match_rules
        return payload


def settings_scope_resolver(settings: AppSettings):
    from app.domain.mocks.policies import ChainedScopeResolver
    from app.infra.scope_resolution import (
        DefaultScopeResolutionStrategy,
        HeaderScopeResolutionStrategy,
        JsonBodyFieldScopeResolutionStrategy,
    )

    return ChainedScopeResolver(
        strategies=[
            HeaderScopeResolutionStrategy(settings.scope_header_name),
            JsonBodyFieldScopeResolutionStrategy(settings.scope_body_field_name),
            DefaultScopeResolutionStrategy(settings.default_scope),
        ]
    )
