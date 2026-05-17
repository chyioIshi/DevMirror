import pytest

from tests.testkit.factories import CommandFactory
from tests.testkit.fakes import FakeMockRepository


@pytest.fixture
def fake_mock_repository() -> FakeMockRepository:
    return FakeMockRepository()


@pytest.fixture
def command_factory() -> CommandFactory:
    return CommandFactory()

