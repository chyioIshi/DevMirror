import pytest

from app.application.request_logs import RequestLogService
from tests.testkit.fakes import FakeRequestLogRepository


@pytest.fixture
def fake_request_log_repository() -> FakeRequestLogRepository:
    return FakeRequestLogRepository()


@pytest.fixture
def request_log_service(
    fake_request_log_repository: FakeRequestLogRepository,
) -> RequestLogService:
    return RequestLogService(fake_request_log_repository)
