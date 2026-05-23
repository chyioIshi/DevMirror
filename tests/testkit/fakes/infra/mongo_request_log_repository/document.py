class FakeMongoRequestLogDocument:
    """Fake Mongo document для unit-тестов MongoRequestLogRepository."""

    def __init__(self) -> None:
        self.insert_called = False

    async def insert(self) -> None:
        self.insert_called = True
