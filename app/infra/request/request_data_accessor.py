"""Request body access helpers for FastAPI requests."""

from typing import Any, Protocol

from fastapi import Request


class RequestDataAccessor(Protocol):
    """Provides safe access to a cached FastAPI request body."""

    async def get_body_bytes(self, request: Request) -> bytes:
        """Returns raw request body bytes.

        Args:
            request: FastAPI request object.

        Returns:
            Raw request body bytes.
        """
        ...

    async def get_text(self, request: Request) -> str | None:
        """Returns request body as text.

        Args:
            request: FastAPI request object.

        Returns:
            UTF-8 text body or ``None`` for empty bodies.
        """
        ...

    async def get_json(self, request: Request) -> Any | None:
        """Returns parsed JSON body.

        Args:
            request: FastAPI request object.

        Returns:
            Parsed JSON value or ``None`` when the body is empty.
        """
        ...
