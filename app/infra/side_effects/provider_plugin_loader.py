"""Loads side effect providers from Python entry points."""

import importlib.metadata
import logging
from typing import Any, NoReturn, cast

from app.application.exceptions import SideEffectProviderAlreadyRegisteredError
from app.application.side_effects import SideEffectProviderRegistry
from app.domain.mocks.ports import SideEffectProvider
from app.infra.exceptions import SideEffectProviderPluginError
from app.infra.side_effects.connection_registry import ConnectionRegistry

logger = logging.getLogger(__name__)

SIDE_EFFECT_PROVIDER_ENTRY_POINT_GROUP = "devmirror.side_effect_providers"


class SideEffectProviderPluginLoader:
    """Loads installed side effect provider plugins into a provider registry."""

    def __init__(
        self,
        *,
        connection_registry: ConnectionRegistry,
        entry_point_group: str = SIDE_EFFECT_PROVIDER_ENTRY_POINT_GROUP,
    ) -> None:
        """Initializes the plugin loader."""
        self._connection_registry = connection_registry
        self._entry_point_group = entry_point_group

    def load_into(self, registry: SideEffectProviderRegistry) -> None:
        """Loads provider factories from entry points and registers created providers."""
        for entry_point in importlib.metadata.entry_points(group=self._entry_point_group):
            factory = self._load_factory(entry_point)
            provider_name = self._validate_factory(factory, entry_point)
            provider = self._create_provider(factory, entry_point)
            self._validate_provider(provider, provider_name, entry_point)
            self._register_provider(registry, provider, entry_point)

    def _load_factory(self, entry_point: importlib.metadata.EntryPoint) -> Any:
        try:
            factory_candidate = entry_point.load()
        except Exception as exc:
            self._raise_plugin_error(
                "Side effect provider plugin entry point could not be imported",
                entry_point,
                error=exc,
            )

        try:
            return factory_candidate() if isinstance(factory_candidate, type) else factory_candidate
        except Exception as exc:
            self._raise_plugin_error(
                "Side effect provider factory could not be initialized",
                entry_point,
                error=exc,
            )

    def _validate_factory(
        self,
        factory: Any,
        entry_point: importlib.metadata.EntryPoint,
    ) -> str:
        provider_name = getattr(factory, "provider", None)
        if not isinstance(provider_name, str) or not provider_name.strip():
            self._raise_plugin_error(
                "Side effect provider factory must define a non-empty provider",
                entry_point,
                details={"field": "provider"},
            )

        create = getattr(factory, "create", None)
        if not callable(create):
            self._raise_plugin_error(
                "Side effect provider factory must define create(connection_registry)",
                entry_point,
                details={"field": "create"},
            )

        return provider_name

    def _create_provider(
        self,
        factory: Any,
        entry_point: importlib.metadata.EntryPoint,
    ) -> SideEffectProvider:
        try:
            return cast(SideEffectProvider, factory.create(self._connection_registry))
        except Exception as exc:
            self._raise_plugin_error(
                "Side effect provider factory create(connection_registry) failed",
                entry_point,
                error=exc,
            )

    def _validate_provider(
        self,
        provider: Any,
        expected_provider_name: str,
        entry_point: importlib.metadata.EntryPoint,
    ) -> None:
        provider_name = getattr(provider, "provider", None)
        if provider_name != expected_provider_name:
            self._raise_plugin_error(
                "Side effect provider name must match factory provider",
                entry_point,
                details={
                    "factory_provider": expected_provider_name,
                    "provider": provider_name,
                },
            )

        if not callable(getattr(provider, "execute", None)):
            self._raise_plugin_error(
                "Side effect provider must define execute(effect, context)",
                entry_point,
                details={"field": "execute"},
            )

    def _register_provider(
        self,
        registry: SideEffectProviderRegistry,
        provider: SideEffectProvider,
        entry_point: importlib.metadata.EntryPoint,
    ) -> None:
        try:
            registry.register(provider)
        except SideEffectProviderAlreadyRegisteredError:
            logger.exception(
                "side_effect_provider_plugin_duplicate",
                extra={
                    "entry_point": entry_point.name,
                    "entry_point_group": self._entry_point_group,
                    "provider": provider.provider,
                },
            )
            raise

        logger.info(
            "side_effect_provider_plugin_loaded",
            extra={
                "entry_point": entry_point.name,
                "entry_point_group": self._entry_point_group,
                "provider": provider.provider,
            },
        )

    def _raise_plugin_error(
        self,
        message: str,
        entry_point: importlib.metadata.EntryPoint,
        *,
        error: Exception | None = None,
        details: dict[str, Any] | None = None,
    ) -> NoReturn:
        error_details = {
            "entry_point": entry_point.name,
            "entry_point_group": self._entry_point_group,
        }
        error_details.update(details or {})
        if error is not None:
            error_details["error"] = str(error)

        logger.exception(message, extra=error_details) if error is not None else logger.error(
            message,
            extra=error_details,
        )
        raise SideEffectProviderPluginError(message=message, details=error_details)
