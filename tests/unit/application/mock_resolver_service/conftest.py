import pytest

from app.application.mocks import (
    MockResolverService,
    MockSessionResolveStrategy,
    RuleMatchingResolveStrategy,
)
from app.application.request_logs import RequestLogService
from app.domain.mocks.policies import MockSelectionPolicy
from app.domain.mocks.services import MockResolutionService, RuleMatcherService
from tests.testkit.fakes import (
    FakeMockRepository,
    FakeRequestLogRepository,
    FakeScopeResolver,
)


@pytest.fixture
def fake_request_log_repository() -> FakeRequestLogRepository:
    return FakeRequestLogRepository()


@pytest.fixture
def request_log_service(
    fake_request_log_repository: FakeRequestLogRepository,
) -> RequestLogService:
    return RequestLogService(fake_request_log_repository)


@pytest.fixture
def fake_scope_resolver() -> FakeScopeResolver:
    return FakeScopeResolver()


@pytest.fixture
def mock_resolver_service(
    fake_mock_repository: FakeMockRepository,
    request_log_service: RequestLogService,
    fake_scope_resolver: FakeScopeResolver,
) -> MockResolverService:
    return MockResolverService(
        strategies=[
            MockSessionResolveStrategy(
                mock_repository=fake_mock_repository,
                request_log_service=request_log_service,
            ),
            RuleMatchingResolveStrategy(
                mock_repository=fake_mock_repository,
                request_log_service=request_log_service,
                scope_resolver=fake_scope_resolver,
                mock_resolution_service=MockResolutionService(
                    rule_matcher=RuleMatcherService(),
                    selection_policy=MockSelectionPolicy(),
                ),
            ),
        ],
    )
