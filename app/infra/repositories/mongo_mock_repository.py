
from collections.abc import Sequence

from beanie import PydanticObjectId
from beanie.operators import In
from pymongo import ASCENDING, DESCENDING

from app.domain.models.enums import HttpMethod
from app.domain.models.mocks.mock import Mock
from app.domain.models.mocks.mock_list_filters import MockListFilters
from app.infra.db.mongo.documents.mock_document import MockDocument
from app.infra.mappers.mock_mapper import MockMapper


class MongoMockRepository:
    """Сохраняет и запрашивает определения моков в MongoDB."""

    async def create(self, mock: Mock) -> Mock:
        """Создаёт новый документ мока и возвращает сохранённую доменную модель."""
        document = MockMapper.to_document(mock)
        await document.insert()
        return MockMapper.to_domain(document)

    async def get_by_id(self, mock_id: str) -> Mock | None:
        """Возвращает мок по идентификатору или ``None`` для некорректного либо отсутствующего id."""
        object_id = self._parse_object_id(mock_id)
        if object_id is None:
            return None
        document = await MockDocument.get(object_id)
        if document is None:
            return None
        return MockMapper.to_domain(document)

    async def list_mocks(
        self, filters: MockListFilters, limit: int = 100, offset: int = 0
    ) -> list[Mock]:
        """Возвращает список моков с учётом фильтров и поддержкой пагинации."""
        query = MockDocument.find_all()

        if filters.path is not None:
            query = query.find(MockDocument.path == filters.path)
        if filters.method is not None:
            query = query.find(MockDocument.method == filters.method)
        if filters.active is not None:
            query = query.find(MockDocument.active == filters.active)
        if filters.scope is not None:
            query = query.find(MockDocument.scope == filters.scope)

        documents = await query.sort(
            [
                (MockDocument.path, ASCENDING),
                (MockDocument.method, ASCENDING),
                (MockDocument.priority, DESCENDING),
                (MockDocument.updated_at, DESCENDING),
            ],
        ).skip(offset).limit(limit).to_list()
        return [MockMapper.to_domain(document) for document in documents]

    async def update(self, mock: Mock) -> Mock:
        """Заменяет существующий Mongo-документ переданным состоянием мока."""
        document = MockMapper.to_document(mock)
        await document.replace()
        return MockMapper.to_domain(document)

    async def delete(self, mock_id: str) -> bool:
        """Удаляет мок по id и сообщает, был ли удалён документ."""
        object_id = self._parse_object_id(mock_id)
        if object_id is None:
            return False
        document = await MockDocument.get(object_id)
        if document is None:
            return False
        await document.delete()
        return True

    async def list_candidates(
        self,
        method: HttpMethod | str,
        path: str,
        scopes: Sequence[str],
    ) -> list[Mock]:
        """Возвращает активные моки, подходящие для обработки runзапроса."""
        normalized_method = method if isinstance(method, HttpMethod) else HttpMethod(method)

        documents = await MockDocument.find(
            MockDocument.method == normalized_method,
            MockDocument.path == path,
            MockDocument.active == True,  # noqa: E712
            In(MockDocument.scope, list(scopes)),
        ).sort(
            [
                (MockDocument.priority, DESCENDING),
                (MockDocument.updated_at, DESCENDING),
                (MockDocument.created_at, DESCENDING),
            ],
        ).to_list()

        return [MockMapper.to_domain(document) for document in documents]

    async def list_active_conflicts(self, mock: Mock) -> list[Mock]:
        """Находит другие активные моки, конфликтующие с переданным моком."""
        if mock.id is None:
            return []
        object_id = self._parse_object_id(mock.id)
        if object_id is None:
            return []

        documents = await MockDocument.find(
            MockDocument.path == mock.path,
            MockDocument.method == mock.method,
            MockDocument.scope == mock.scope,
            MockDocument.active == True,  # noqa: E712
            MockDocument.id != object_id,
        ).to_list()

        return [MockMapper.to_domain(document) for document in documents]

    @staticmethod
    def _parse_object_id(mock_id: str) -> PydanticObjectId | None:
        """Безопасно преобразует строковый идентификатор в ``PydanticObjectId``."""
        try:
            return PydanticObjectId(mock_id)
        except Exception:
            return None
