from dataclasses import dataclass

from app.infra.celery import state


@dataclass(slots=True)
class FakeSettings:
    pass


@dataclass(slots=True)
class FakeContainer:
    close_count: int = 0

    async def aclose(self) -> None:
        self.close_count += 1


class TestCeleryRuntime:
    def teardown_method(self) -> None:
        state.WorkerState.container = None

    async def test_startup_creates_container_once(self, monkeypatch) -> None:
        containers: list[FakeContainer] = []

        def create_container(settings: FakeSettings) -> FakeContainer:
            container = FakeContainer()
            containers.append(container)
            return container

        monkeypatch.setattr(state, "get_app_settings", FakeSettings)
        monkeypatch.setattr(state, "AppContainer", create_container)

        await state.WorkerState.startup()
        await state.WorkerState.startup()
        container = state.WorkerState.get_container()

        assert containers == [container]

    def test_get_container_requires_initialized_worker_state(self) -> None:
        state.WorkerState.container = None

        try:
            state.WorkerState.get_container()
        except RuntimeError as exc:
            assert str(exc) == "Celery worker container is not initialized"
        else:
            raise AssertionError("Expected RuntimeError")

    async def test_shutdown_closes_and_resets_container(self) -> None:
        container = FakeContainer()
        state.WorkerState.container = container

        await state.WorkerState.shutdown()

        assert container.close_count == 1
        assert state.WorkerState.container is None

    async def test_shutdown_is_safe_without_container(self) -> None:
        state.WorkerState.container = None

        await state.WorkerState.shutdown()

        assert state.WorkerState.container is None
