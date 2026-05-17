import pytest
from pymongo.errors import NetworkTimeout

from app.infra.exceptions import DatabaseConnectionError
from app.infra.repositories import mongo_mock_repository
from app.infra.repositories.mongo_mock_repository import MongoMockRepository
from tests.testkit.fakes import (
    FakeCandidateMockDocument,
    FakeMongoMockDocument,
    FakeMongoMockMapper,
    FakeMongoMockQuery,
)


class TestMongoMockRepository:
    """Проверяет MongoMockRepository."""

    async def test_add_inserts_document_and_returns_domain_mock(
        self,
        mock_factory,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Проверяет сохранение нового мока."""
        mock = mock_factory.create_mock()
        saved_mock = mock_factory.create_mock(mock_id="000000000000000000000001")
        mapper = FakeMongoMockMapper
        mapper.document = FakeMongoMockDocument()
        mapper.domain_mock = saved_mock
        monkeypatch.setattr(mongo_mock_repository, "MockMapper", mapper)

        result = await MongoMockRepository().add(mock)

        assert mapper.document.insert_called is True
        assert result is saved_mock

    async def test_get_by_id_returns_none_for_invalid_id(self) -> None:
        """Проверяет None для некорректного id."""
        result = await MongoMockRepository().get_by_id("not-object-id")

        assert result is None

    async def test_get_by_id_maps_existing_document(
        self,
        mock_factory,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Проверяет получение найденного документа."""
        saved_mock = mock_factory.create_mock(mock_id="000000000000000000000001")
        mapper = FakeMongoMockMapper
        mapper.domain_mock = saved_mock
        document = object()

        async def fake_get(_: object) -> object:
            return document

        monkeypatch.setattr(mongo_mock_repository.MockDocument, "get", fake_get)
        monkeypatch.setattr(mongo_mock_repository, "MockMapper", mapper)

        result = await MongoMockRepository().get_by_id("000000000000000000000001")

        assert result is saved_mock

    async def test_get_by_id_wraps_connection_errors(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Проверяет обертку ошибок подключения к Mongo."""

        async def fake_get(_: object) -> object:
            raise NetworkTimeout("timeout")

        monkeypatch.setattr(mongo_mock_repository.MockDocument, "get", fake_get)

        with pytest.raises(DatabaseConnectionError) as error:
            await MongoMockRepository().get_by_id("000000000000000000000001")

        assert error.value.details == {
            "operation": "get_by_id",
            "mock_id": "000000000000000000000001",
        }

    async def test_save_replaces_document_and_returns_domain_mock(
        self,
        mock_factory,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Проверяет замену существующего документа."""
        mock = mock_factory.create_mock(mock_id="000000000000000000000001")
        mapper = FakeMongoMockMapper
        mapper.document = FakeMongoMockDocument()
        mapper.domain_mock = mock
        monkeypatch.setattr(mongo_mock_repository, "MockMapper", mapper)

        result = await MongoMockRepository().save(mock)

        assert mapper.document.replace_called is True
        assert result is mock

    async def test_remove_deletes_existing_document(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Проверяет удаление найденного документа."""
        document = FakeMongoMockDocument()

        async def fake_get(_: object) -> FakeMongoMockDocument:
            return document

        monkeypatch.setattr(mongo_mock_repository.MockDocument, "get", fake_get)

        result = await MongoMockRepository().remove("000000000000000000000001")

        assert result is True
        assert document.delete_called is True

    async def test_remove_returns_false_for_missing_document(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Проверяет False при отсутствии документа."""

        async def fake_get(_: object) -> None:
            return None

        monkeypatch.setattr(mongo_mock_repository.MockDocument, "get", fake_get)

        result = await MongoMockRepository().remove("000000000000000000000001")

        assert result is False

    async def test_list_candidates_normalizes_method_and_maps_documents(
        self,
        mock_factory,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Проверяет поиск кандидатов и маппинг документов."""
        saved_mock = mock_factory.create_mock(mock_id="000000000000000000000001")
        mapper = FakeMongoMockMapper
        mapper.domain_mock = saved_mock
        query = FakeMongoMockQuery(documents=[object()])
        FakeCandidateMockDocument.query = query

        monkeypatch.setattr(mongo_mock_repository, "MockDocument", FakeCandidateMockDocument)
        monkeypatch.setattr(mongo_mock_repository, "MockMapper", mapper)

        result = await MongoMockRepository().list_candidates("GET", "/users", ["global"])

        assert result == [saved_mock]
        assert len(FakeCandidateMockDocument.captured_args) == 4
        assert query.sort_called is True
