import pytest

from app.infra.db.mongo.documents import MockDocument, RequestLogDocument


@pytest.fixture
def beanie_document_constructors(monkeypatch: pytest.MonkeyPatch) -> None:
    """Отключает проверку Mongo-коллекции для unit-тестов мапперов."""

    def empty_collection(_: type[object]) -> None:
        return None

    collection_getter = classmethod(empty_collection)
    monkeypatch.setattr(MockDocument, "get_pymongo_collection", collection_getter)
    monkeypatch.setattr(RequestLogDocument, "get_pymongo_collection", collection_getter)
