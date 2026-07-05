"""Mock repository port."""

from collections.abc import Sequence
from typing import Protocol

from app.domain.mocks.models.mock import Mock
from app.domain.mocks.models.mock_list_filters import MockListFilters
from app.domain.shared import HttpMethod


class MockRepository(Protocol):
    """Describes persistence and retrieval operations for mocks."""

    async def add(self, mock: Mock) -> Mock:
        """Persists a new mock definition.

        Args:
            mock: Mock to persist.

        Returns:
            Persisted mock.
        """
        ...

    async def get_by_id(self, mock_id: str) -> Mock | None:
        """Returns a mock by id.

        Args:
            mock_id: Mock identifier.

        Returns:
            Mock when found; otherwise ``None``.
        """
        ...

    async def save(self, mock: Mock) -> Mock:
        """Persists changes to an existing mock.

        Args:
            mock: Mock with updated state.

        Returns:
            Saved mock.
        """
        ...

    async def remove(self, mock_id: str) -> bool:
        """Removes a mock.

        Args:
            mock_id: Mock identifier.

        Returns:
            True when the operation removed a mock; otherwise False.
        """
        ...

    async def list_mocks(
        self,
        filters: MockListFilters,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Mock]:
        """Returns mocks with pagination support.

        Args:
            filters: Filters applied to the query.
            limit: Maximum number of records to return.
            offset: Number of records to skip.

        Returns:
            List of matching mocks.
        """
        ...

    async def list_candidates(
        self,
        method: HttpMethod,
        path: str,
        scopes: Sequence[str],
    ) -> list[Mock]:
        """Returns mocks that can be considered during resolution.

        Args:
            method: Request HTTP method.
            path: Request path.
            scopes: Scopes allowed for resolution.

        Returns:
            Candidate mocks for request resolution.
        """
        ...

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
            session_id: Session identifier from the request header.

        Returns:
            Latest active session mock when found; otherwise ``None``.
        """
        ...
