from fastapi import Response
from fastapi.responses import JSONResponse

from app.domain.mocks.models import MockResponse
from app.infra.response.mock_response_builder import MockResponseBuilder


class TestMockResponseBuilder:
    """Проверяет сборку FastAPI response из Mock."""

    def test_build_returns_empty_response_when_body_is_none(self, mock_factory) -> None:
        """Проверяет ответ без json body."""
        mock = mock_factory.create_mock(
            response_status_code=204,
            response_headers={"x-test": "yes"},
            response_body=None,
        )

        response = MockResponseBuilder().build(mock)

        assert isinstance(response, Response)
        assert not isinstance(response, JSONResponse)
        assert response.status_code == 204
        assert response.headers["x-test"] == "yes"
        assert response.body == b""

    def test_build_returns_json_response_when_body_exists(self, mock_factory) -> None:
        """Проверяет json response при наличии body."""
        mock = mock_factory.create_mock(
            response_status_code=201,
            response_headers={"x-test": "yes"},
            response_body={"ok": True},
        )

        response = MockResponseBuilder().build(mock)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 201
        assert response.headers["x-test"] == "yes"
        assert response.body == b'{"ok":true}'

    def test_build_response_returns_json_response_when_body_exists(self) -> None:
        response = MockResponseBuilder().build_response(
            MockResponse(status_code=202, body={"ok": True}),
        )

        assert isinstance(response, JSONResponse)
        assert response.status_code == 202
        assert response.body == b'{"ok":true}'
