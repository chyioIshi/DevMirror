from typing import Any, Protocol

from fastapi import Request


class RequestDataAccessor(Protocol):
    """Описывает доступ к кэшированным представлениям тела FastAPI-запроса.

    Это infra-уровневый порт: он привязан к транспорту FastAPI и используется
    адаптерами, которые превращают сырой Request в доменный RequestContext.
    """

    async def get_body_bytes(self, request: Request) -> bytes:
        """Возвращает сырые байты тела запроса."""
        ...

    async def get_text(self, request: Request) -> str | None:
        """Возвращает тело запроса как декодированный текст, если оно доступно."""
        ...

    async def get_json(self, request: Request) -> Any | None:
        """Возвращает разобранное JSON-тело, если оно доступно."""
        ...
