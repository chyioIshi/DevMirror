import pytest

from app.application.request_logs import RequestLogService
from app.domain.request_logs.models import RequestLogRecord
from tests.testkit.factories import RequestFactory
from tests.testkit.fakes import FakeRequestLogRepository


class TestListAndClear:
    """Проверяет чтение и очистку журнала запросов."""

    @pytest.mark.asyncio
    async def test_list_records_uses_requested_pagination(
        self,
        request_log_service: RequestLogService,
        fake_request_log_repository: FakeRequestLogRepository,
        request_factory: RequestFactory,
    ) -> None:
        """Проверяет, что чтение передает limit и offset в репозиторий."""
        fake_request_log_repository.records.extend(
            RequestLogRecord(
                request_context=request_factory.create_request_context(path=f"/item-{index}"),
            )
            for index in range(3)
        )

        records = await request_log_service.list_records(limit=1, offset=1)

        assert len(records) == 1
        assert records[0].request_context.path == "/item-1"
        assert fake_request_log_repository.list_records_calls == [(1, 1)]

    @pytest.mark.asyncio
    async def test_clear_removes_records(
        self,
        request_log_service: RequestLogService,
        fake_request_log_repository: FakeRequestLogRepository,
        request_factory: RequestFactory,
    ) -> None:
        """Проверяет, что очистка удаляет записи журнала."""
        fake_request_log_repository.records.append(
            RequestLogRecord(
                request_context=request_factory.create_request_context(path="/item"),
            ),
        )

        await request_log_service.clear()

        assert fake_request_log_repository.records == []
        assert fake_request_log_repository.clear_calls == 1
