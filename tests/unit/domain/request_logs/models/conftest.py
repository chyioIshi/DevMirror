import pytest

from tests.testkit.factories import RequestFactory


@pytest.fixture
def request_factory() -> RequestFactory:
    return RequestFactory()
