import pytest

from app.infra.request.request_data_reader import RequestDataReader


class TestRequestDataReader:
    """Проверяет чтение и кэширование тела FastAPI request."""

    @pytest.mark.asyncio
    async def test_get_body_bytes_caches_body(self, request_with_body) -> None:
        """Проверяет, что bytes тела сохраняются в state."""
        request = request_with_body(b'{"ok": true}')
        reader = RequestDataReader()

        first = await reader.get_body_bytes(request)
        second = await reader.get_body_bytes(request)

        assert first == b'{"ok": true}'
        assert second == b'{"ok": true}'
        assert request.state.cached_body_bytes == b'{"ok": true}'

    @pytest.mark.asyncio
    async def test_get_text_returns_none_for_empty_body(self, request_with_body) -> None:
        """Проверяет, что пустое тело возвращает None."""
        request = request_with_body(b"")

        result = await RequestDataReader().get_text(request)

        assert result is None
        assert request.state.cached_body_text is None

    @pytest.mark.asyncio
    async def test_get_json_parses_valid_json(self, request_with_body) -> None:
        """Проверяет разбор валидного json."""
        request = request_with_body(b'{"ok": true}')

        result = await RequestDataReader().get_json(request)

        assert result == {"ok": True}
        assert request.state.cached_body_json == {"ok": True}

    @pytest.mark.asyncio
    async def test_get_json_returns_none_for_invalid_json(self, request_with_body) -> None:
        """Проверяет, что невалидный json возвращает None."""
        request = request_with_body(b"not-json")

        result = await RequestDataReader().get_json(request)

        assert result is None
        assert request.state.cached_body_json is None
