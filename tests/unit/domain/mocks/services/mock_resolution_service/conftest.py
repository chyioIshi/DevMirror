import pytest

from app.domain.mocks.policies import MockSelectionPolicy
from app.domain.mocks.services import MockResolutionService, RuleMatcherService


@pytest.fixture
def mock_resolution_service() -> MockResolutionService:
    return MockResolutionService(
        rule_matcher=RuleMatcherService(),
        selection_policy=MockSelectionPolicy(),
    )
