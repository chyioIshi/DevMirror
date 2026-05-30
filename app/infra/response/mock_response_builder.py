"""HTTP response builder for resolved mocks."""

from fastapi import Response
from fastapi.responses import JSONResponse

from app.domain.mocks.models import Mock


class MockResponseBuilder:
    """Builds FastAPI responses from resolved mock configuration."""

    def build(self, mock: Mock) -> Response:
        """Builds an HTTP response from a resolved mock response model.

        Args:
            mock: Domain mock model whose response should be returned.

        Returns:
            FastAPI JSON response matching the mock response configuration.
        """
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
