from tests.testkit.fakes.infra.mongo_mock_repository.query import FakeMongoMockQuery


class FakeCandidateMockDocument:
    """Fake document class для построения запроса кандидатов."""

    method = "method"
    path = "path"
    active = "active"
    scope = "scope"
    mock_session_id = "mock_session_id"
    priority = "priority"
    updated_at = "updated_at"
    created_at = "created_at"
    query = FakeMongoMockQuery(documents=[])
    captured_args: list[object] = []

    @classmethod
    def find(cls, *args: object) -> FakeMongoMockQuery:
        cls.captured_args = list(args)
        return cls.query
