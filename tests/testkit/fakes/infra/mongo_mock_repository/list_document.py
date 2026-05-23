from tests.testkit.fakes.infra.mongo_mock_repository.query import FakeMongoMockQuery


class FakeListMockDocument:
    """Fake document class для построения запроса списка моков."""

    path = "path"
    method = "method"
    active = "active"
    scope = "scope"
    priority = "priority"
    updated_at = "updated_at"
    query = FakeMongoMockQuery(documents=[])

    @classmethod
    def find_all(cls) -> FakeMongoMockQuery:
        return cls.query
