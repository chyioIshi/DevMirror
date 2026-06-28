import json
from collections.abc import Callable

import httpx
import pytest

from app.domain.mocks.models import SideEffect, SideEffectContext, SideEffectType
from app.infra.exceptions import InvalidSideEffectProviderConfigError
from app.infra.side_effects import ConnectionConfig, ConnectionRegistry
from app.infra.side_effects.providers import HttpCallbackSideEffectProvider


class FakeAsyncClient:
    def __init__(self) -> None:
        self.request_count = 0
        self.is_closed = False

    async def request(self, *args: object, **kwargs: object) -> httpx.Response:
        self.request_count += 1
        return httpx.Response(status_code=200, text="ok")

    async def aclose(self) -> None:
        self.is_closed = True


class TestHttpCallbackSideEffectProvider:
    async def test_reuses_injected_http_client_between_executions(
        self,
        connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        client = FakeAsyncClient()
        effect = side_effect_factory(
            type=SideEffectType.HTTP_CALLBACK,
            provider="http",
            target={"connection": "main-http", "path": "callbacks"},
        )
        provider = HttpCallbackSideEffectProvider(
            connection_registry=connection_registry,
            client=client,
        )

        await provider.execute(effect, side_effect_context)
        await provider.execute(effect, side_effect_context)

        assert client.request_count == 2
        assert client.is_closed is False

    async def test_sends_request_to_base_url_and_target_path(
        self,
        connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        requests: list[httpx.Request] = []

        async def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return httpx.Response(status_code=202, text="accepted")

        effect = side_effect_factory(
            type=SideEffectType.HTTP_CALLBACK,
            provider="http",
            target={"connection": "main-http", "path": "/callbacks/orders"},
            payload_template={"entity_id": "entity-1"},
        )

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            provider = HttpCallbackSideEffectProvider(
                connection_registry=connection_registry,
                client=client,
            )

            result = await provider.execute(effect, side_effect_context)

        assert result.success is True
        assert result.details == {
            "status_code": 202,
            "response_text_preview": "accepted",
        }
        assert len(requests) == 1
        assert str(requests[0].url) == "https://callback.test/api/callbacks/orders"
        assert requests[0].method == "POST"
        assert json.loads(requests[0].content) == {"entity_id": "entity-1"}

    async def test_supports_absolute_target_url(
        self,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        connection_registry = ConnectionRegistry(
            connections=[
                ConnectionConfig(
                    name="main-http",
                    provider="http",
                    settings={
                        "base_url": "https://callback.test/api",
                        "allow_absolute_url": True,
                    },
                ),
            ],
        )
        requests: list[httpx.Request] = []

        async def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return httpx.Response(status_code=200, text="ok")

        effect = side_effect_factory(
            type=SideEffectType.HTTP_CALLBACK,
            provider="http",
            target={
                "connection": "main-http",
                "url": "https://override.test/callback",
            },
        )

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            provider = HttpCallbackSideEffectProvider(
                connection_registry=connection_registry,
                client=client,
            )

            await provider.execute(effect, side_effect_context)

        assert str(requests[0].url) == "https://override.test/callback"

    async def test_rejects_absolute_target_url_without_connection_opt_in(
        self,
        connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        effect = side_effect_factory(
            type=SideEffectType.HTTP_CALLBACK,
            provider="http",
            target={
                "connection": "main-http",
                "url": "https://override.test/callback",
            },
        )
        provider = HttpCallbackSideEffectProvider(
            connection_registry=connection_registry,
            client=FakeAsyncClient(),
        )

        with pytest.raises(
            InvalidSideEffectProviderConfigError,
            match="allow_absolute_url",
        ):
            await provider.execute(effect, side_effect_context)

    async def test_rejects_non_http_or_https_scheme(
        self,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        registry = ConnectionRegistry(
            connections=[
                ConnectionConfig(
                    name="main-http",
                    provider="http",
                    settings={
                        "base_url": "https://callback.test/api",
                        "allow_absolute_url": True,
                    },
                ),
            ],
        )
        effect = side_effect_factory(
            type=SideEffectType.HTTP_CALLBACK,
            provider="http",
            target={
                "connection": "main-http",
                "url": "ftp://callback.test/file",
            },
        )
        provider = HttpCallbackSideEffectProvider(
            connection_registry=registry,
            client=FakeAsyncClient(),
        )

        with pytest.raises(
            InvalidSideEffectProviderConfigError,
            match="absolute http or https URL",
        ):
            await provider.execute(effect, side_effect_context)

    async def test_merges_default_headers_and_options_headers(
        self,
        connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        requests: list[httpx.Request] = []

        async def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return httpx.Response(status_code=200)

        effect = side_effect_factory(
            type=SideEffectType.HTTP_CALLBACK,
            provider="http",
            target={"connection": "main-http", "path": "callbacks"},
            options={
                "headers": {
                    "X-Extra": "extra",
                    "X-Override": "options",
                },
            },
        )

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            provider = HttpCallbackSideEffectProvider(
                connection_registry=connection_registry,
                client=client,
            )

            await provider.execute(effect, side_effect_context)

        assert requests[0].headers["x-default"] == "default"
        assert requests[0].headers["x-extra"] == "extra"
        assert requests[0].headers["x-override"] == "options"

    @pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
    async def test_body_methods_send_json_body(
        self,
        method: str,
        connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        requests: list[httpx.Request] = []

        async def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return httpx.Response(status_code=200)

        effect = side_effect_factory(
            type=SideEffectType.HTTP_CALLBACK,
            provider="http",
            target={"connection": "main-http", "path": "callbacks"},
            payload_template={"entity_id": "entity-1"},
            options={"method": method},
        )

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            provider = HttpCallbackSideEffectProvider(
                connection_registry=connection_registry,
                client=client,
            )

            await provider.execute(effect, side_effect_context)

        assert requests[0].method == method
        assert json.loads(requests[0].content) == {"entity_id": "entity-1"}

    async def test_get_method_does_not_send_json_body(
        self,
        connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        requests: list[httpx.Request] = []

        async def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return httpx.Response(status_code=200)

        effect = side_effect_factory(
            type=SideEffectType.HTTP_CALLBACK,
            provider="http",
            target={"connection": "main-http", "path": "callbacks"},
            options={"method": "GET"},
        )

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            provider = HttpCallbackSideEffectProvider(
                connection_registry=connection_registry,
                client=client,
            )

            await provider.execute(effect, side_effect_context)

        assert requests[0].method == "GET"
        assert requests[0].content == b""

    async def test_rejects_invalid_method(
        self,
        connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        effect = side_effect_factory(
            type=SideEffectType.HTTP_CALLBACK,
            provider="http",
            target={"connection": "main-http", "path": "callbacks"},
            options={"method": "TRACE"},
        )
        provider = HttpCallbackSideEffectProvider(
            connection_registry=connection_registry,
            client=FakeAsyncClient(),
        )

        with pytest.raises(
            InvalidSideEffectProviderConfigError,
            match="options.method",
        ):
            await provider.execute(effect, side_effect_context)

    async def test_returns_failure_for_non_2xx_response(
        self,
        connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(status_code=503, text="service unavailable")

        effect = side_effect_factory(
            type=SideEffectType.HTTP_CALLBACK,
            provider="http",
            target={"connection": "main-http", "path": "callbacks"},
        )

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            provider = HttpCallbackSideEffectProvider(
                connection_registry=connection_registry,
                client=client,
            )

            result = await provider.execute(effect, side_effect_context)

        assert result.success is False
        assert result.error == "HTTP callback returned status 503"
        assert result.details == {
            "status_code": 503,
            "response_text_preview": "service unavailable",
        }

    async def test_http_error_returns_failed_execution_result(
        self,
        connection_registry: ConnectionRegistry,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        async def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection failed", request=request)

        effect = side_effect_factory(
            type=SideEffectType.HTTP_CALLBACK,
            provider="http",
            target={"connection": "main-http", "path": "callbacks"},
        )

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            provider = HttpCallbackSideEffectProvider(
                connection_registry=connection_registry,
                client=client,
            )

            result = await provider.execute(effect, side_effect_context)

        assert result.success is False
        assert result.error == "connection failed"

    async def test_rejects_non_http_connection(
        self,
        side_effect_context: SideEffectContext,
        side_effect_factory: Callable[..., SideEffect],
    ) -> None:
        registry = ConnectionRegistry(
            connections=[
                ConnectionConfig(
                    name="main-kafka",
                    provider="kafka",
                    settings={"base_url": "https://callback.test"},
                )
            ]
        )
        effect = side_effect_factory(
            type=SideEffectType.HTTP_CALLBACK, provider="http", target={"connection": "main-kafka"}
        )
        provider = HttpCallbackSideEffectProvider(
            connection_registry=registry,
            client=FakeAsyncClient(),
        )

        with pytest.raises(
            InvalidSideEffectProviderConfigError,
            match="must reference an http connection",
        ):
            await provider.execute(effect, side_effect_context)
