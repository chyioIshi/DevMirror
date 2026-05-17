class FakeMongoMockDocument:
    """Fake Mongo document для unit-тестов MongoMockRepository."""

    def __init__(self) -> None:
        self.insert_called = False
        self.replace_called = False
        self.delete_called = False

    async def insert(self) -> None:
        self.insert_called = True

    async def replace(self) -> None:
        self.replace_called = True

    async def delete(self) -> None:
        self.delete_called = True

