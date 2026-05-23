from app.domain.request_logs.models import RequestLogRecord
from tests.testkit.fakes.infra.mongo_request_log_repository.document import (
    FakeMongoRequestLogDocument,
)


class FakeMongoRequestLogMapper:
    """Fake mapper для unit-тестов MongoRequestLogRepository."""

    document = FakeMongoRequestLogDocument()
    domain_record: RequestLogRecord

    @classmethod
    def to_document(cls, _: RequestLogRecord) -> FakeMongoRequestLogDocument:
        return cls.document

    @classmethod
    def to_domain(cls, _: object) -> RequestLogRecord:
        return cls.domain_record
