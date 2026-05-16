import pytest

from app.domain.mocks.policies import MockSelectionPolicy
from app.domain.mocks.services import MockResolutionService, RuleMatcherService
from tests.testkit.factories import MockFactory, RequestFactory


@pytest.fixture
def mock_resolution_service() -> MockResolutionService:
    return MockResolutionService(
        rule_matcher=RuleMatcherService(),
        selection_policy=MockSelectionPolicy(),
    )


@pytest.fixture
def mock_factory() -> MockFactory:
    return MockFactory()


@pytest.fixture
def request_factory() -> RequestFactory:
    return RequestFactory()
