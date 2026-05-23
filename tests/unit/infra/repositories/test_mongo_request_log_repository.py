from app.domain.request_logs.models import RequestLogRecord
from app.infra.repositories import mongo_request_log_repository
from app.infra.repositories.mongo_request_log_repository import MongoRequestLogRepository
from tests.testkit.fakes import (
    FakeMongoRequestLogDocument,
    FakeMongoRequestLogMapper,
    FakeMongoRequestLogQuery,
)


class TestMongoRequestLogRepository:
    """Проверяет MongoRequestLogRepository."""

    async def test_write_inserts_document_and_returns_domain_record(
        self,
        request_factory,
        monkeypatch,
    ) -> None:
        """Проверяет создание request log."""
        record = RequestLogRecord(request_context=request_factory.create_request_context())
        saved_record = RequestLogRecord(
            id="000000000000000000000001",
            request_context=request_factory.create_request_context(),
        )
        mapper = FakeMongoRequestLogMapper
        mapper.document = FakeMongoRequestLogDocument()
        mapper.domain_record = saved_record
        monkeypatch.setattr(mongo_request_log_repository, "RequestLogMapper", mapper)

        result = await MongoRequestLogRepository().write(record)

        assert mapper.document.insert_called is True
        assert result is saved_record

    async def test_list_records_sorts_limits_and_maps_documents(
        self,
        request_factory,
        monkeypatch,
    ) -> None:
        """Проверяет получение request logs."""
        saved_record = RequestLogRecord(
            id="000000000000000000000001",
            request_context=request_factory.create_request_context(),
        )
        mapper = FakeMongoRequestLogMapper
        mapper.domain_record = saved_record
        query = FakeMongoRequestLogQuery(documents=[object()])

        monkeypatch.setattr(
            mongo_request_log_repository.RequestLogDocument,
            "find_all",
            lambda: query,
        )
        monkeypatch.setattr(mongo_request_log_repository, "RequestLogMapper", mapper)

        result = await MongoRequestLogRepository().list_records(limit=10, offset=5)

        assert result == [saved_record]
        assert query.sort_called is True
        assert query.skip_value == 5
        assert query.limit_value == 10

    async def test_clear_deletes_all_documents(self, monkeypatch) -> None:
        """Проверяет очистку журнала."""
        query = FakeMongoRequestLogQuery(documents=[])
        monkeypatch.setattr(
            mongo_request_log_repository.RequestLogDocument,
            "find_all",
            lambda: query,
        )

        await MongoRequestLogRepository().clear()

        assert query.delete_called is True
