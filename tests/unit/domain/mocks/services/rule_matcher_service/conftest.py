import pytest

from app.domain.mocks.services import RuleMatcherService
from tests.testkit.factories import MockFactory, RequestFactory


@pytest.fixture
def request_factory() -> RequestFactory:
    return RequestFactory()


@pytest.fixture
def mock_factory() -> MockFactory:
    return MockFactory()


@pytest.fixture
def matcher() -> RuleMatcherService:
    return RuleMatcherService()
