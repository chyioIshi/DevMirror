from typing import Any

import pytest

from app.config import Settings
from app.infra.db.mongo import bootstrap
from app.infra.db.mongo.documents import MockDocument, RequestLogDocument


class _FakeMongoClient:
    def __init__(self, dsn: object) -> None:
        self.dsn = dsn
        self.requested_databases: list[str] = []

    def __getitem__(self, database_name: str) -> str:
        self.requested_databases.append(database_name)
        return database_name


class TestMongoBootstrap:
    """Проверяет bootstrap Mongo без реального подключения."""

    async def test_init_mongo_initializes_beanie_with_documents(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Проверяет создание клиента и инициализацию Beanie."""
        created_clients: list[_FakeMongoClient] = []
        captured_kwargs: dict[str, Any] = {}

        def fake_client(dsn: object) -> _FakeMongoClient:
            client = _FakeMongoClient(dsn)
            created_clients.append(client)
            return client

        async def fake_init_beanie(**kwargs: Any) -> None:
            captured_kwargs.update(kwargs)

        monkeypatch.setattr(bootstrap, "AsyncMongoClient", fake_client)
        monkeypatch.setattr(bootstrap, "init_beanie", fake_init_beanie)
        settings = Settings(
            mongo_dsn="mongodb://localhost:27017",
            mongo_database="devmirror_test",
        )

        client = await bootstrap.init_mongo(settings)

        assert client is created_clients[0]
        assert str(client.dsn) == "mongodb://localhost:27017"
        assert client.requested_databases == ["devmirror_test"]
        assert captured_kwargs["database"] == "devmirror_test"
        assert captured_kwargs["document_models"] == [MockDocument, RequestLogDocument]
