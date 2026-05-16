import pytest

from app.domain.mocks.services import RuleMatcherService


@pytest.fixture
def matcher() -> RuleMatcherService:
    return RuleMatcherService()
