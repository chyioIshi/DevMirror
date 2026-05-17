from collections.abc import Awaitable, Callable

import pytest
from starlette.requests import Request

type Receive = Callable[[], Awaitable[dict[str, object]]]


@pytest.fixture
def request_with_body() -> Callable[[bytes], Request]:
    def _factory(body: bytes) -> Request:
        received = False

        async def receive() -> dict[str, object]:
            nonlocal received
            if received:
                return {"type": "http.request", "body": b"", "more_body": False}
            received = True
            return {"type": "http.request", "body": body, "more_body": False}

        return Request(
            {
                "type": "http",
                "method": "POST",
                "path": "/test",
                "headers": [],
                "query_string": b"",
            },
            receive=receive,
        )

    return _factory
