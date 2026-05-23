from collections.abc import AsyncIterator

import httpx
import pytest
from fastapi import FastAPI

from app.api.error_handlers import register_exception_handlers
from app.api.routes import (
    catch_all_router,
    health_router,
    mock_admin_router,
    request_log_router,
)
from app.config import AppSettings
from app.di import (
    get_app_settings,
    get_mock_management_service,
    get_mock_resolver_service,
    get_mock_response_builder,
    get_request_context_resolver,
    get_request_log_service,
)
from app.domain.mocks.models.resolution import ResolvedMock, RuleMatchResult
from app.domain.request_logs.models import RequestLogRecord
from app.infra.response import MockResponseBuilder
from tests.testkit.factories import MockFactory, RequestFactory
from tests.testkit.fakes import (
    FakeMockManagementService,
    FakeMockResolverService,
    FakeRequestContextResolver,
    FakeRequestLogService,
)


@pytest.fixture
def mock_factory() -> MockFactory:
    return MockFactory()


@pytest.fixture
def request_factory() -> RequestFactory:
    return RequestFactory()


@pytest.fixture
def api_settings() -> AppSettings:
    return AppSettings(
        admin_prefix="/admin/mocks",
        request_log_prefix="/admin/request-logs",
        health_prefix="/health",
    )


@pytest.fixture
def api_app(
    api_settings: AppSettings,
    fake_mock_management_service: FakeMockManagementService,
    fake_mock_resolver_service: FakeMockResolverService,
    fake_request_context_resolver: FakeRequestContextResolver,
    fake_request_log_service: FakeRequestLogService,
) -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(health_router, prefix="/health")
    app.include_router(mock_admin_router, prefix="/admin/mocks")
    app.include_router(request_log_router, prefix="/admin/request-logs")
    app.include_router(catch_all_router)
    app.dependency_overrides[get_app_settings] = lambda: api_settings
    app.dependency_overrides[get_mock_management_service] = lambda: fake_mock_management_service
    app.dependency_overrides[get_mock_resolver_service] = lambda: fake_mock_resolver_service
    app.dependency_overrides[get_request_context_resolver] = lambda: fake_request_context_resolver
    app.dependency_overrides[get_mock_response_builder] = lambda: MockResponseBuilder()
    app.dependency_overrides[get_request_log_service] = lambda: fake_request_log_service
    return app


@pytest.fixture
async def api_client(api_app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=api_app),
        base_url="http://test",
    ) as client:
        yield client


@pytest.fixture
async def api_client_no_raise(api_app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=api_app, raise_app_exceptions=False),
        base_url="http://test",
    ) as client:
        yield client


@pytest.fixture
def fake_mock_management_service(mock_factory) -> FakeMockManagementService:
    created_mock = mock_factory.create_mock(
        mock_id="000000000000000000000001",
        name="created-mock",
        path="/created",
    )
    fetched_mock = mock_factory.create_mock(
        mock_id="000000000000000000000002",
        name="fetched-mock",
        path="/fetched",
    )
    updated_mock = mock_factory.create_mock(
        mock_id="000000000000000000000003",
        name="updated-mock",
        path="/updated",
    )
    activated_mock = mock_factory.create_mock(
        mock_id="000000000000000000000004",
        name="activated-mock",
        path="/activated",
        active=True,
    )
    deactivated_mock = mock_factory.create_mock(
        mock_id="000000000000000000000005",
        name="deactivated-mock",
        path="/deactivated",
        active=False,
    )
    return FakeMockManagementService(
        created_mock=created_mock,
        fetched_mock=fetched_mock,
        listed_mocks=[created_mock, fetched_mock],
        updated_mock=updated_mock,
        activated_mock=activated_mock,
        deactivated_mock=deactivated_mock,
    )


@pytest.fixture
def fake_request_log_service(request_factory) -> FakeRequestLogService:
    record = RequestLogRecord(
        id="record-1",
        request_context=request_factory.create_request_context(path="/created"),
    )
    return FakeRequestLogService(records=[record])


@pytest.fixture
def fake_request_context_resolver(
    request_factory: RequestFactory,
) -> FakeRequestContextResolver:
    request_context = request_factory.create_request_context(path="/external")
    return FakeRequestContextResolver(request_context=request_context)


@pytest.fixture
def fake_mock_resolver_service(mock_factory: MockFactory) -> FakeMockResolverService:
    mock = mock_factory.create_mock(
        mock_id="000000000000000000000006",
        path="/external",
        active=True,
        response_status_code=202,
        response_body={"message": "matched"},
    )
    resolved_mock = ResolvedMock(
        mock=mock,
        scope="global",
        rule_result=RuleMatchResult(matched=True, score=1),
    )
    return FakeMockResolverService(resolved_mock=resolved_mock)
