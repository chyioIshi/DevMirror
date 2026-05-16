import pytest

from tests.testkit.factories import MockFactory, RequestFactory


@pytest.fixture
def request_factory() -> RequestFactory:
    return RequestFactory()


@pytest.fixture
def mock_factory() -> MockFactory:
    return MockFactory()
