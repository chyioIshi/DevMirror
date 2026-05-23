from fastapi import Response
from fastapi.responses import JSONResponse

from app.domain.mocks.models import Mock


class MockResponseBuilder:
    """Собирает объекты ответа FastAPI из сохранённых определений моков."""

    def build(self, mock: Mock) -> Response:
        """Создаёт HTTP-ответ на основе конфигурации ответа мока."""
        response_definition = mock.response

        if response_definition.body is None:
            return Response(
                status_code=response_definition.status_code,
                headers=response_definition.headers,
            )

        return JSONResponse(
            status_code=response_definition.status_code,
            headers=response_definition.headers,
            content=response_definition.body,
        )
