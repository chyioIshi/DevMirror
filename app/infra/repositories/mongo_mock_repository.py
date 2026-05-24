from collections.abc import Sequence

from beanie import PydanticObjectId, SortDirection
from beanie.operators import In
from pymongo.errors import (
    AutoReconnect,
    ConnectionFailure,
    NetworkTimeout,
    ServerSelectionTimeoutError,
)

from app.domain.mocks.models import Mock, MockListFilters
from app.domain.shared import HttpMethod
from app.infra.db.mongo.documents import MockDocument
from app.infra.exceptions import DatabaseConnectionError, RepositoryError
from app.infra.mappers import MockMapper

_CONNECTION_ERRORS = (
    AutoReconnect,
    ConnectionFailure,
    NetworkTimeout,
    ServerSelectionTimeoutError,
)


class MongoMockRepository:
    """Сохраняет и запрашивает определения моков в MongoDB."""

    async def add(self, mock: Mock) -> Mock:
        """Создаёт новый документ мока и возвращает сохранённую доменную модель."""
        try:
            document = MockMapper.to_document(mock)
            await document.insert()
            return MockMapper.to_domain(document)
        except _CONNECTION_ERRORS as exc:
            raise DatabaseConnectionError(details={"operation": "add"}) from exc
        except Exception as exc:
            raise RepositoryError(details={"operation": "add"}) from exc

    async def get_by_id(self, mock_id: str) -> Mock | None:
        """Возвращает мок по идентификатору.

        Возвращает ``None`` для некорректного либо отсутствующего id.
        """
        object_id = self._parse_object_id(mock_id)
        if object_id is None:
            return None
        try:
            document = await MockDocument.get(object_id)
            if document is None:
                return None
            return MockMapper.to_domain(document)
        except _CONNECTION_ERRORS as exc:
            raise DatabaseConnectionError(
                details={"operation": "get_by_id", "mock_id": mock_id},
            ) from exc
        except Exception as exc:
            raise RepositoryError(
                details={"operation": "get_by_id", "mock_id": mock_id},
            ) from exc

    async def save(self, mock: Mock) -> Mock:
        """Заменяет существующий Mongo-документ переданным состоянием мока."""
        try:
            document = MockMapper.to_document(mock)
            await document.replace()
            return MockMapper.to_domain(document)
        except _CONNECTION_ERRORS as exc:
            raise DatabaseConnectionError(
                details={"operation": "save", "mock_id": mock.id},
            ) from exc
        except Exception as exc:
            raise RepositoryError(
                details={"operation": "save", "mock_id": mock.id},
            ) from exc

    async def remove(self, mock_id: str) -> bool:
        """Удаляет мок по id и сообщает, был ли удалён документ."""
        object_id = self._parse_object_id(mock_id)
        if object_id is None:
            return False
        try:
            document = await MockDocument.get(object_id)
            if document is None:
                return False
            await document.delete()
            return True
        except _CONNECTION_ERRORS as exc:
            raise DatabaseConnectionError(
                details={"operation": "remove", "mock_id": mock_id},
            ) from exc
        except Exception as exc:
            raise RepositoryError(
                details={"operation": "remove", "mock_id": mock_id},
            ) from exc

    async def list_mocks(
        self,
        filters: MockListFilters,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Mock]:
        """Возвращает список моков с учётом фильтров и поддержкой пагинации."""
        try:
            query = MockDocument.find_all()

            if filters.path is not None:
                query = query.find(MockDocument.path == filters.path)
            if filters.method is not None:
                query = query.find(MockDocument.method == filters.method)
            if filters.active is not None:
                query = query.find(MockDocument.active == filters.active)
            if filters.scope is not None:
                query = query.find(MockDocument.scope == filters.scope)

            documents = (
                await query.sort(
                    [
                        ("path", SortDirection.ASCENDING),
                        ("method", SortDirection.ASCENDING),
                        ("priority", SortDirection.DESCENDING),
                        ("updated_at", SortDirection.DESCENDING),
                    ],
                )
                .skip(offset)
                .limit(limit)
                .to_list()
            )
            return [MockMapper.to_domain(document) for document in documents]
        except _CONNECTION_ERRORS as exc:
            raise DatabaseConnectionError(
                details={"operation": "list_mocks", "limit": limit, "offset": offset},
            ) from exc
        except Exception as exc:
            raise RepositoryError(
                details={"operation": "list_mocks", "limit": limit, "offset": offset},
            ) from exc

    async def list_candidates(
        self,
        method: HttpMethod | str,
        path: str,
        scopes: Sequence[str],
    ) -> list[Mock]:
        """Возвращает активные моки, подходящие для обработки runзапроса."""
        normalized_method = method if isinstance(method, HttpMethod) else HttpMethod(method)

        try:
            documents = (
                await MockDocument.find(
                    MockDocument.method == normalized_method,
                    MockDocument.path == path,
                    MockDocument.active == True,  # noqa: E712
                    In(MockDocument.scope, list(scopes)),
                )
                .sort(
                    [
                        ("priority", SortDirection.DESCENDING),
                        ("updated_at", SortDirection.DESCENDING),
                        ("created_at", SortDirection.DESCENDING),
                    ],
                )
                .to_list()
            )

            return [MockMapper.to_domain(document) for document in documents]
        except _CONNECTION_ERRORS as exc:
            raise DatabaseConnectionError(
                details={
                    "operation": "list_candidates",
                    "method": str(normalized_method),
                    "path": path,
                    "scopes": list(scopes),
                },
            ) from exc
        except Exception as exc:
            raise RepositoryError(
                details={
                    "operation": "list_candidates",
                    "method": str(normalized_method),
                    "path": path,
                    "scopes": list(scopes),
                },
            ) from exc

    @staticmethod
    def _parse_object_id(mock_id: str) -> PydanticObjectId | None:
        """Безопасно преобразует строковый идентификатор в ``PydanticObjectId``."""
        try:
            return PydanticObjectId(mock_id)
        except Exception:
            return None
