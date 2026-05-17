from app.domain.mocks.models import Mock


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


class FakeMongoMockMapper:
    """Fake mapper для unit-тестов MongoMockRepository."""

    document = FakeMongoMockDocument()
    domain_mock: Mock

    @classmethod
    def to_document(cls, _: Mock) -> FakeMongoMockDocument:
        return cls.document

    @classmethod
    def to_domain(cls, _: object) -> Mock:
        return cls.domain_mock


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


class FakeCandidateMockDocument:
    """Fake document class для построения запроса кандидатов."""

    method = "method"
    path = "path"
    active = "active"
    scope = "scope"
    priority = "priority"
    updated_at = "updated_at"
    created_at = "created_at"
    query = FakeMongoMockQuery(documents=[])
    captured_args: list[object] = []

    @classmethod
    def find(cls, *args: object) -> FakeMongoMockQuery:
        cls.captured_args = list(args)
        return cls.query
