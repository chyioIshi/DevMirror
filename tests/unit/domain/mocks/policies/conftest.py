import pytest

from tests.testkit.factories import MockFactory


@pytest.fixture
def mock_factory() -> MockFactory:
    return MockFactory()
