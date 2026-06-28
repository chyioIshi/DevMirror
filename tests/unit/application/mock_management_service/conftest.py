import pytest

from app.application.mocks import MockManagementService
from app.domain.mocks.policies import MockActivationPolicy
from app.domain.mocks.services import MockConflictService
from tests.testkit.fakes import FakeMockRepository


@pytest.fixture
def fake_mock_service(
    fake_mock_repository: FakeMockRepository,
) -> MockManagementService:
    return MockManagementService(
        repository=fake_mock_repository,
        conflict_service=MockConflictService(),
        activation_policy=MockActivationPolicy(),
    )
