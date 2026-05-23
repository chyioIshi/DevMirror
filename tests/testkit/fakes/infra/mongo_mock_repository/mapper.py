from app.domain.mocks.models import Mock
from tests.testkit.fakes.infra.mongo_mock_repository.document import (
    FakeMongoMockDocument,
)


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
