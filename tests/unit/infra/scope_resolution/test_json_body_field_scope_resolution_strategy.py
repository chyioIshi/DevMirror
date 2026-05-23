import pytest

from app.infra.scope_resolution import JsonBodyFieldScopeResolutionStrategy


class TestJsonBodyFieldScopeResolutionStrategy:
    """Проверяет стратегию разрешения scope из json тела."""

    @pytest.mark.asyncio
    async def test_returns_field_value_from_dict_body(self, request_factory) -> None:
        """Проверяет, что стратегия возвращает значение поля из dict body."""
        strategy = JsonBodyFieldScopeResolutionStrategy("scope")
        ctx = request_factory.create_request_context(body={"scope": "user1"})

        assert await strategy.resolve(ctx) == "user1"

    @pytest.mark.asyncio
    async def test_returns_none_when_body_is_not_dict(self, request_factory) -> None:
        """Проверяет, что стратегия возвращает None для body не dict типа."""
        strategy = JsonBodyFieldScopeResolutionStrategy("scope")
        ctx = request_factory.create_request_context(body="raw text")

        assert await strategy.resolve(ctx) is None

    @pytest.mark.asyncio
    async def test_returns_none_when_field_missing(self, request_factory) -> None:
        """Проверяет, что стратегия возвращает None при отсутствии поля."""
        strategy = JsonBodyFieldScopeResolutionStrategy("scope")
        ctx = request_factory.create_request_context(body={"other": "x"})

        assert await strategy.resolve(ctx) is None

    @pytest.mark.asyncio
    async def test_coerces_non_string_value_to_str(self, request_factory) -> None:
        """Проверяет, что стратегия приводит нестроковое значение к строке."""
        strategy = JsonBodyFieldScopeResolutionStrategy("scope")
        ctx = request_factory.create_request_context(body={"scope": 42})

        assert await strategy.resolve(ctx) == "42"
