"""Registry for side effect providers."""

from app.application.exceptions import (
    SideEffectProviderAlreadyRegisteredError,
    SideEffectProviderNotFoundError,
)
from app.domain.mocks.ports import SideEffectProvider


class SideEffectProviderRegistry:
    """Stores side effect providers by provider name."""

    def __init__(self) -> None:
        self._providers: dict[str, SideEffectProvider] = {}

    def register(self, provider: SideEffectProvider) -> None:
        """Registers a provider by its provider name."""
        if provider.provider in self._providers:
            raise SideEffectProviderAlreadyRegisteredError(provider=provider.provider)

        self._providers[provider.provider] = provider

    def get(self, provider_name: str) -> SideEffectProvider:
        """Returns a provider by name."""
        try:
            return self._providers[provider_name]
        except KeyError as exc:
            raise SideEffectProviderNotFoundError(provider=provider_name) from exc
