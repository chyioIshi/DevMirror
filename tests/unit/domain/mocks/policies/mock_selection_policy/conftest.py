import pytest

from app.domain.mocks.models.resolution import RuleMatchResult
from app.domain.mocks.policies import MockSelectionPolicy


@pytest.fixture
def policy() -> MockSelectionPolicy:
    return MockSelectionPolicy()


@pytest.fixture
def zero_score_result() -> RuleMatchResult:
    return RuleMatchResult(matched=True, score=0)
