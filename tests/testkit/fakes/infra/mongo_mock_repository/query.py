class FakeMongoMockQuery:
    """Fake query для unit-тестов MongoMockRepository."""

    def __init__(self, documents: list[object]) -> None:
        self.documents = documents
        self.sort_called = False

    def sort(self, _: object) -> "FakeMongoMockQuery":
        self.sort_called = True
        return self

    async def to_list(self) -> list[object]:
        return self.documents

