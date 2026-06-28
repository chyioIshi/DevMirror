from dataclasses import dataclass
from typing import Any

import pytest

from app.application.exceptions import SideEffectProviderAlreadyRegisteredError
from app.application.side_effects import SideEffectProviderRegistry
from app.infra.exceptions import SideEffectProviderPluginError
from app.infra.side_effects import (
    SIDE_EFFECT_PROVIDER_ENTRY_POINT_GROUP,
    ConnectionRegistry,
    SideEffectProviderPluginLoader,
)
from tests.testkit.fakes.application import FakeSideEffectProvider


@dataclass(slots=True)
class FakeEntryPoint:
    name: str
    loaded: Any
    error: Exception | None = None

    def load(self) -> Any:
        if self.error is not None:
            raise self.error
        return self.loaded


class FakeProviderFactory:
    provider = "fake"
    connection_registry: ConnectionRegistry | None = None

    def create(self, connection_registry: ConnectionRegistry) -> FakeSideEffectProvider:
        type(self).connection_registry = connection_registry
        return FakeSideEffectProvider(provider=self.provider)


class TestSideEffectProviderPluginLoader:
    def test_loads_provider_factory_from_entry_point(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        connection_registry = ConnectionRegistry()
        registry = SideEffectProviderRegistry()
        entry_point = FakeEntryPoint(name="fake", loaded=FakeProviderFactory)
        self._patch_entry_points(monkeypatch, [entry_point])

        SideEffectProviderPluginLoader(connection_registry=connection_registry).load_into(registry)

        assert registry.get("fake").provider == "fake"
        assert FakeProviderFactory.connection_registry is connection_registry

    def test_rejects_factory_without_provider(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        class FactoryWithoutProvider:
            def create(self, connection_registry: ConnectionRegistry) -> FakeSideEffectProvider:
                return FakeSideEffectProvider(provider="fake")

        self._patch_entry_points(
            monkeypatch,
            [FakeEntryPoint(name="broken", loaded=FactoryWithoutProvider)],
        )

        with pytest.raises(SideEffectProviderPluginError) as exc_info:
            SideEffectProviderPluginLoader(
                connection_registry=ConnectionRegistry(),
            ).load_into(SideEffectProviderRegistry())

        assert exc_info.value.details["entry_point"] == "broken"
        assert exc_info.value.details["field"] == "provider"

    def test_rejects_factory_without_create(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        class FactoryWithoutCreate:
            provider = "fake"

        self._patch_entry_points(
            monkeypatch,
            [FakeEntryPoint(name="broken", loaded=FactoryWithoutCreate)],
        )

        with pytest.raises(SideEffectProviderPluginError) as exc_info:
            SideEffectProviderPluginLoader(
                connection_registry=ConnectionRegistry(),
            ).load_into(SideEffectProviderRegistry())

        assert exc_info.value.details["entry_point"] == "broken"
        assert exc_info.value.details["field"] == "create"

    def test_rejects_provider_with_mismatched_name(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        class MismatchedFactory:
            provider = "fake"

            def create(self, connection_registry: ConnectionRegistry) -> FakeSideEffectProvider:
                return FakeSideEffectProvider(provider="other")

        self._patch_entry_points(
            monkeypatch,
            [FakeEntryPoint(name="broken", loaded=MismatchedFactory)],
        )

        with pytest.raises(SideEffectProviderPluginError) as exc_info:
            SideEffectProviderPluginLoader(
                connection_registry=ConnectionRegistry(),
            ).load_into(SideEffectProviderRegistry())

        assert exc_info.value.details == {
            "entry_point": "broken",
            "entry_point_group": SIDE_EFFECT_PROVIDER_ENTRY_POINT_GROUP,
            "factory_provider": "fake",
            "provider": "other",
        }

    def test_rejects_provider_without_execute(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        class ProviderWithoutExecute:
            provider = "fake"

        class Factory:
            provider = "fake"

            def create(self, connection_registry: ConnectionRegistry) -> ProviderWithoutExecute:
                return ProviderWithoutExecute()

        self._patch_entry_points(monkeypatch, [FakeEntryPoint(name="broken", loaded=Factory)])

        with pytest.raises(SideEffectProviderPluginError) as exc_info:
            SideEffectProviderPluginLoader(
                connection_registry=ConnectionRegistry(),
            ).load_into(SideEffectProviderRegistry())

        assert exc_info.value.details["entry_point"] == "broken"
        assert exc_info.value.details["field"] == "execute"

    def test_rejects_entry_point_import_error(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        self._patch_entry_points(
            monkeypatch,
            [FakeEntryPoint(name="broken", loaded=None, error=RuntimeError("boom"))],
        )

        with pytest.raises(SideEffectProviderPluginError) as exc_info:
            SideEffectProviderPluginLoader(
                connection_registry=ConnectionRegistry(),
            ).load_into(SideEffectProviderRegistry())

        assert exc_info.value.details["error"] == "boom"
        assert exc_info.value.details["entry_point"] == "broken"

    def test_rejects_factory_create_error(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        class BrokenFactory:
            provider = "fake"

            def create(self, connection_registry: ConnectionRegistry) -> FakeSideEffectProvider:
                raise RuntimeError("boom")

        self._patch_entry_points(monkeypatch, [FakeEntryPoint(name="broken", loaded=BrokenFactory)])

        with pytest.raises(SideEffectProviderPluginError) as exc_info:
            SideEffectProviderPluginLoader(
                connection_registry=ConnectionRegistry(),
            ).load_into(SideEffectProviderRegistry())

        assert exc_info.value.details["error"] == "boom"

    def test_detects_duplicate_provider(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        registry = SideEffectProviderRegistry()
        registry.register(FakeSideEffectProvider(provider="fake"))
        self._patch_entry_points(
            monkeypatch,
            [FakeEntryPoint(name="fake", loaded=FakeProviderFactory)],
        )

        with pytest.raises(SideEffectProviderAlreadyRegisteredError):
            SideEffectProviderPluginLoader(
                connection_registry=ConnectionRegistry(),
            ).load_into(registry)

    def _patch_entry_points(
        self,
        monkeypatch: pytest.MonkeyPatch,
        entry_points: list[FakeEntryPoint],
    ) -> None:
        monkeypatch.setattr(
            "app.infra.side_effects.provider_plugin_loader.importlib.metadata.entry_points",
            lambda group: entry_points,
        )
