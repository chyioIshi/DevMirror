"""MongoDB repository implementation for mocks."""

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
    """Persists and queries mock definitions in MongoDB."""

    async def add(self, mock: Mock) -> Mock:
        """Creates a new mock document and returns the persisted domain model.

        Args:
            mock: Domain mock model to persist.

        Returns:
            Persisted mock.

        Raises:
            DatabaseConnectionError: If MongoDB connection fails.
            RepositoryError: If persistence fails for another reason.
        """
        try:
            document = MockMapper.to_document(mock)
            await document.insert()
            return MockMapper.to_domain(document)
        except _CONNECTION_ERRORS as exc:
            raise DatabaseConnectionError(details={"operation": "add"}) from exc
        except Exception as exc:
            raise RepositoryError(details={"operation": "add"}) from exc

    async def get_by_id(self, mock_id: str) -> Mock | None:
        """Returns a mock by id.

        Args:
            mock_id: Mock identifier.

        Returns:
            Mock when found; otherwise ``None``.

        Raises:
            DatabaseConnectionError: If MongoDB connection fails.
            RepositoryError: If lookup fails for another reason.
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
        """Replaces an existing Mongo document with the provided mock state.

        Args:
            mock: Domain mock model to persist.

        Returns:
            Saved mock.

        Raises:
            DatabaseConnectionError: If MongoDB connection fails.
            RepositoryError: If persistence fails for another reason.
        """
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
        """Deletes a mock by id.

        Args:
            mock_id: Mock identifier.

        Returns:
            True when a document was deleted; otherwise False.

        Raises:
            DatabaseConnectionError: If MongoDB connection fails.
            RepositoryError: If deletion fails for another reason.
        """
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
        """Returns mocks with filters and pagination support.

        Args:
            filters: Filters applied to the query.
            limit: Maximum number of mocks to return.
            offset: Number of mocks to skip.

        Returns:
            Matching mocks.

        Raises:
            DatabaseConnectionError: If MongoDB connection fails.
            RepositoryError: If query execution fails for another reason.
        """
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
        """Returns active mocks suitable for request resolution.

        Args:
            method: Request HTTP method.
            path: Request path.
            scopes: Scopes allowed for resolution.

        Returns:
            Candidate mocks.

        Raises:
            DatabaseConnectionError: If MongoDB connection fails.
            RepositoryError: If query execution fails for another reason.
        """
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

    async def find_latest_by_session_id(
        self,
        method: HttpMethod | str,
        path: str,
        session_id: str,
    ) -> Mock | None:
        """Returns the newest active mock for a route and session id.

        Args:
            method: Request HTTP method.
            path: Request path.
            session_id: Session id from the ``mock-session-id`` header.

        Returns:
            Latest active session mock when found; otherwise ``None``.

        Raises:
            DatabaseConnectionError: If MongoDB connection fails.
            RepositoryError: If query execution fails for another reason.
        """
        normalized_method = method if isinstance(method, HttpMethod) else HttpMethod(method)

        try:
            documents = (
                await MockDocument.find(
                    MockDocument.method == normalized_method,
                    MockDocument.path == path,
                    MockDocument.mock_session_id == session_id,
                    MockDocument.active == True,  # noqa: E712
                )
                .sort(
                    [
                        ("updated_at", SortDirection.DESCENDING),
                        ("created_at", SortDirection.DESCENDING),
                        ("_id", SortDirection.DESCENDING),
                    ],
                )
                .limit(1)
                .to_list()
            )
            if not documents:
                return None
            return MockMapper.to_domain(documents[0])
        except _CONNECTION_ERRORS as exc:
            raise DatabaseConnectionError(
                details={
                    "operation": "find_latest_by_session_id",
                    "method": str(normalized_method),
                    "path": path,
                    "session_id": session_id,
                },
            ) from exc
        except Exception as exc:
            raise RepositoryError(
                details={
                    "operation": "find_latest_by_session_id",
                    "method": str(normalized_method),
                    "path": path,
                    "session_id": session_id,
                },
            ) from exc

    @staticmethod
    def _parse_object_id(mock_id: str) -> PydanticObjectId | None:
        """Safely converts a string identifier to `PydanticObjectId`.

        Args:
            mock_id: String mock identifier.

        Returns:
            Parsed object id or ``None`` when the value is invalid.
        """
        try:
            return PydanticObjectId(mock_id)
        except Exception:
            return None
