import pytest

from app.application.services import MockManagementService
from app.domain.mocks.policies import MockActivationPolicy
from app.domain.mocks.services import MockConflictService
from tests.testkit.factories import CommandFactory, MockFactory
from tests.testkit.fakes import FakeMockRepository


@pytest.fixture
def fake_mock_repo() -> FakeMockRepository:
    return FakeMockRepository()


@pytest.fixture
def fake_mock_service(fake_mock_repo: FakeMockRepository) -> MockManagementService:
    return MockManagementService(
        repository=fake_mock_repo,
        conflict_service=MockConflictService(),
        activation_policy=MockActivationPolicy(),
    )


@pytest.fixture
def mock_factory() -> MockFactory:
    return MockFactory()


@pytest.fixture
def command_factory() -> CommandFactory:
    return CommandFactory()
