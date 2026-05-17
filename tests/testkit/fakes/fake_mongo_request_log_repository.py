from app.domain.request_logs.models import RequestLogRecord


class FakeMongoRequestLogDocument:
    """Fake Mongo document для unit-тестов MongoRequestLogRepository."""

    def __init__(self) -> None:
        self.insert_called = False

    async def insert(self) -> None:
        self.insert_called = True


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


class FakeMongoRequestLogQuery:
    """Fake query для unit-тестов MongoRequestLogRepository."""

    def __init__(self, documents: list[object]) -> None:
        self.documents = documents
        self.sort_called = False
        self.skip_value: int | None = None
        self.limit_value: int | None = None
        self.delete_called = False

    def sort(self, _: object) -> "FakeMongoRequestLogQuery":
        self.sort_called = True
        return self

    def skip(self, offset: int) -> "FakeMongoRequestLogQuery":
        self.skip_value = offset
        return self

    def limit(self, limit: int) -> "FakeMongoRequestLogQuery":
        self.limit_value = limit
        return self

    async def to_list(self) -> list[object]:
        return self.documents

    async def delete(self) -> None:
        self.delete_called = True
