"""HTTP callback side effect provider."""

from typing import Any, Final
from urllib.parse import urljoin, urlparse

import httpx

from app.domain.mocks.models import (
    SideEffect,
    SideEffectContext,
    SideEffectExecutionResult,
    SideEffectType,
)
from app.helpers.side_effect_provider_validation import SideEffectProviderValidation
from app.infra.exceptions import InvalidSideEffectProviderConfigError
from app.infra.side_effects.connection_config import ConnectionConfig
from app.infra.side_effects.connection_registry import ConnectionRegistry

_ALLOWED_METHODS: Final = {"GET", "POST", "PUT", "PATCH", "DELETE"}
_BODY_METHODS: Final = {"POST", "PUT", "PATCH", "DELETE"}
_RESPONSE_TEXT_PREVIEW_LENGTH: Final = 500


class HttpCallbackSideEffectProvider:
    """Executes rendered ``http_callback`` side effects through HTTP requests.

    The application dispatcher renders ``payload_template`` and ``options`` before provider
    execution. This provider treats ``effect.payload_template`` as the rendered JSON payload
    and ``effect.options`` as rendered execution options; it never renders templates itself.
    """

    provider = "http"

    def __init__(
        self,
        connection_registry: ConnectionRegistry,
        client: httpx.AsyncClient,
    ) -> None:
        """Initializes the provider with connection configs and a reusable HTTP client."""
        self._connection_registry = connection_registry
        self._client = client

    async def execute(
        self,
        effect: SideEffect,
        context: SideEffectContext,
    ) -> SideEffectExecutionResult:
        """Executes a rendered HTTP callback side effect."""

        _ = context

        if effect.type != SideEffectType.HTTP_CALLBACK:
            raise InvalidSideEffectProviderConfigError(
                "HTTP callback provider supports only http_callback side effects",
                details={"type": effect.type.value},
            )

        connection = self._get_connection(effect.target)
        settings = connection.settings
        rendered_payload = effect.payload_template
        rendered_options = effect.options
        method = self._method(rendered_options)
        url = self._url(effect.target, settings)
        headers = self._headers(settings, rendered_options)
        timeout = self._timeout(settings)

        try:
            response = await self._send_request(
                method=method,
                url=url,
                headers=headers,
                payload=rendered_payload,
                timeout=timeout,
            )
        except httpx.HTTPError as exc:
            return SideEffectExecutionResult(
                provider=self.provider,
                success=False,
                error=str(exc),
            )

        success = 200 <= response.status_code < 300
        return SideEffectExecutionResult(
            provider=self.provider,
            success=success,
            details={
                "status_code": response.status_code,
                "response_text_preview": response.text[:_RESPONSE_TEXT_PREVIEW_LENGTH],
            },
            error=None if success else f"HTTP callback returned status {response.status_code}",
        )

    async def _send_request(
        self,
        *,
        method: str,
        url: str,
        headers: dict[str, str],
        payload: Any,
        timeout: float | None,
    ) -> httpx.Response:
        request_kwargs: dict[str, Any] = {"headers": headers}
        if timeout is not None:
            request_kwargs["timeout"] = timeout
        if method in _BODY_METHODS:
            request_kwargs["json"] = payload

        return await self._client.request(method, url, **request_kwargs)

    def _get_connection(self, target: dict[str, Any]) -> ConnectionConfig:
        connection_name = SideEffectProviderValidation.optional_string(
            target, "connection", subject="HTTP callback"
        )
        if connection_name is None:
            raise InvalidSideEffectProviderConfigError(
                "HTTP callback target.connection must be configured",
                details={"field": "target.connection"},
            )

        connection = self._connection_registry.get(connection_name)
        if connection.provider != self.provider:
            raise InvalidSideEffectProviderConfigError(
                "HTTP callback target.connection must reference an http connection",
                details={
                    "field": "target.connection",
                    "connection": connection_name,
                    "provider": connection.provider,
                },
            )
        return connection

    def _url(self, target: dict[str, Any], settings: dict[str, Any]) -> str:
        override_url = SideEffectProviderValidation.optional_string(
            target, "url", subject="HTTP callback"
        )
        if override_url is not None:
            if settings.get("allow_absolute_url") is not True:
                raise InvalidSideEffectProviderConfigError(
                    "HTTP callback target.url requires connection.settings.allow_absolute_url",
                    details={"field": "connection.settings.allow_absolute_url"},
                )
            self._validate_absolute_url(override_url, "target.url")
            return override_url

        base_url = SideEffectProviderValidation.required_string(
            settings,
            "base_url",
            "connection.settings.base_url",
            subject="HTTP callback",
        )
        self._validate_absolute_url(base_url, "connection.settings.base_url")

        path = SideEffectProviderValidation.optional_string(target, "path", subject="HTTP callback")
        if path is None:
            return base_url

        return urljoin(f"{base_url.rstrip('/')}/", path.lstrip("/"))

    def _method(self, options: dict[str, Any]) -> str:
        raw_method = options.get("method", "POST")
        if not isinstance(raw_method, str):
            raise InvalidSideEffectProviderConfigError(
                "HTTP callback options.method must be a string",
                details={"field": "options.method"},
            )

        method = raw_method.upper()
        if method not in _ALLOWED_METHODS:
            raise InvalidSideEffectProviderConfigError(
                "HTTP callback options.method must be one of: "
                f"{', '.join(sorted(_ALLOWED_METHODS))}",
                details={"field": "options.method", "method": raw_method},
            )
        return method

    def _headers(
        self,
        settings: dict[str, Any],
        options: dict[str, Any],
    ) -> dict[str, str]:
        headers = SideEffectProviderValidation.string_mapping(
            settings.get("default_headers"),
            "connection.settings.default_headers",
            subject="HTTP callback",
        )
        headers.update(
            SideEffectProviderValidation.string_mapping(
                options.get("headers"),
                "options.headers",
                subject="HTTP callback",
            )
        )
        return headers

    def _timeout(self, settings: dict[str, Any]) -> float | None:
        timeout = settings.get("timeout_seconds")
        if timeout is None:
            return None
        if isinstance(timeout, int | float) and not isinstance(timeout, bool) and timeout > 0:
            return float(timeout)
        raise InvalidSideEffectProviderConfigError(
            "HTTP callback connection.settings.timeout_seconds must be positive",
            details={"field": "connection.settings.timeout_seconds"},
        )

    def _validate_absolute_url(self, value: str, field: str) -> None:
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise InvalidSideEffectProviderConfigError(
                f"HTTP callback {field} must be an absolute http or https URL",
                details={"field": field},
            )
