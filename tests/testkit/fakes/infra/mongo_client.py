class FakeMongoClient:
    """Fake Mongo client для проверки lifecycle приложения."""

    def __init__(self) -> None:
        self.close_called = False

    def close(self) -> None:
        self.close_called = True
