import pytest

from app.application.request_logs import RequestLogService
from app.domain.request_logs.models import RequestLogRecord, RequestLogVerificationExpectation
from app.domain.shared import HttpMethod
from tests.testkit.factories import RequestFactory
from tests.testkit.fakes import FakeRequestLogRepository


class TestVerify:
    """Проверяет верификацию журнала запросов."""

    @pytest.mark.asyncio
    async def test_verify_matches_when_expected_count_equals_actual_count(
        self,
        request_log_service: RequestLogService,
        fake_request_log_repository: FakeRequestLogRepository,
        request_factory: RequestFactory,
    ) -> None:
        """Проверяет успешную верификацию по точному количеству."""
        fake_request_log_repository.records.extend(
            [
                RequestLogRecord(
                    request_context=request_factory.create_request_context(path="/orders"),
                ),
                RequestLogRecord(
                    request_context=request_factory.create_request_context(path="/orders"),
                ),
                RequestLogRecord(
                    request_context=request_factory.create_request_context(path="/users"),
                ),
            ],
        )

        result = await request_log_service.verify(
            RequestLogVerificationExpectation(
                path="/orders",
                method=HttpMethod.GET,
                expected_count=2,
            ),
        )

        assert result.matched is True
        assert result.actual_count == 2

    @pytest.mark.asyncio
    async def test_verify_fails_when_expected_count_differs(
        self,
        request_log_service: RequestLogService,
        fake_request_log_repository: FakeRequestLogRepository,
        request_factory: RequestFactory,
    ) -> None:
        """Проверяет ошибку верификации при другом количестве."""
        fake_request_log_repository.records.append(
            RequestLogRecord(
                request_context=request_factory.create_request_context(path="/orders"),
            ),
        )

        result = await request_log_service.verify(
            RequestLogVerificationExpectation(
                path="/orders",
                method=HttpMethod.GET,
                expected_count=2,
            ),
        )

        assert result.matched is False
        assert result.actual_count == 1

    @pytest.mark.asyncio
    async def test_verify_without_expected_count_requires_any_match(
        self,
        request_log_service: RequestLogService,
        fake_request_log_repository: FakeRequestLogRepository,
        request_factory: RequestFactory,
    ) -> None:
        """Проверяет, что без expected_count достаточно одного совпадения."""
        fake_request_log_repository.records.append(
            RequestLogRecord(
                request_context=request_factory.create_request_context(path="/orders"),
            ),
        )

        result = await request_log_service.verify(
            RequestLogVerificationExpectation(
                path="/orders",
                method=HttpMethod.GET,
            ),
        )

        assert result.matched is True
        assert result.actual_count == 1
