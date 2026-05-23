class FakeMongoMockDocument:
    """Fake Mongo document для unit-тестов MongoMockRepository."""

    def __init__(
        self,
        *,
        insert_error: Exception | None = None,
        replace_error: Exception | None = None,
        delete_error: Exception | None = None,
    ) -> None:
        self.insert_error = insert_error
        self.replace_error = replace_error
        self.delete_error = delete_error
        self.insert_called = False
        self.replace_called = False
        self.delete_called = False

    async def insert(self) -> None:
        self.insert_called = True
        if self.insert_error is not None:
            raise self.insert_error

    async def replace(self) -> None:
        self.replace_called = True
        if self.replace_error is not None:
            raise self.replace_error

    async def delete(self) -> None:
        self.delete_called = True
        if self.delete_error is not None:
            raise self.delete_error
