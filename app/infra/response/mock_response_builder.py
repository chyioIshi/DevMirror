"""HTTP response builder for resolved mocks."""

from fastapi import Response
from fastapi.responses import JSONResponse

from app.domain.mocks.models import Mock, MockResponse


class MockResponseBuilder:
    """Builds FastAPI responses from resolved mock configuration."""

    def build(self, mock: Mock) -> Response:
        """Builds an HTTP response from a resolved mock response model.

        Args:
            mock: Domain mock model whose response should be returned.

        Returns:
            FastAPI JSON response matching the mock response configuration.
        """
        return self.build_response(mock.response)

    def build_response(self, response_definition: MockResponse) -> Response:
        """Builds an HTTP response from a domain mock response model."""
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
