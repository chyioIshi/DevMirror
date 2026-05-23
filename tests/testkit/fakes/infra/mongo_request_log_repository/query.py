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
