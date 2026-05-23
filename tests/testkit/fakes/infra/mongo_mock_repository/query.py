class FakeMongoMockQuery:
    """Fake query для unit-тестов MongoMockRepository."""

    def __init__(self, documents: list[object]) -> None:
        self.documents = documents
        self.find_calls: list[object] = []
        self.limit_value: int | None = None
        self.skip_value: int | None = None
        self.sort_called = False

    def find(self, condition: object) -> "FakeMongoMockQuery":
        self.find_calls.append(condition)
        return self

    def sort(self, _: object) -> "FakeMongoMockQuery":
        self.sort_called = True
        return self

    def skip(self, value: int) -> "FakeMongoMockQuery":
        self.skip_value = value
        return self

    def limit(self, value: int) -> "FakeMongoMockQuery":
        self.limit_value = value
        return self

    async def to_list(self) -> list[object]:
        return self.documents
