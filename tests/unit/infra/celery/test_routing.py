from app.domain.mocks.models import SideEffect, SideEffectType
from app.infra.celery.routing import CeleryQueueRouter


class TestCeleryQueueRouter:
    def test_routes_side_effects_by_type(self) -> None:
        router = CeleryQueueRouter()

        assert (
            router.queue_for(
                SideEffect(
                    type=SideEffectType.MESSAGE_PUBLISH,
                    provider="kafka",
                    target={"topic": "events"},
                    payload_template={"ok": True},
                ),
            )
            == "side_effects.kafka"
        )
        assert (
            router.queue_for(
                SideEffect(
                    type=SideEffectType.HTTP_CALLBACK,
                    provider="http",
                    target={"connection": "callback"},
                    payload_template={"ok": True},
                ),
            )
            == "side_effects.http"
        )

    def test_routes_db_batch_to_db_queue(self) -> None:
        router = CeleryQueueRouter()
        side_effects = [
            SideEffect(
                type=SideEffectType.DB_INSERT,
                provider="mongo",
                target={"collection": "events"},
                payload_template={"ok": True},
            ),
            SideEffect(
                type=SideEffectType.DB_UPDATE,
                provider="postgres",
                target={"table": "events"},
                payload_template={"ok": True},
            ),
        ]

        assert router.queue_for_batch(side_effects) == "side_effects.db"

    def test_routes_mixed_batch_to_default_queue(self) -> None:
        router = CeleryQueueRouter(default_queue="side_effects.default")
        side_effects = [
            SideEffect(
                type=SideEffectType.MESSAGE_PUBLISH,
                provider="kafka",
                target={"topic": "events"},
                payload_template={"ok": True},
            ),
            SideEffect(
                type=SideEffectType.HTTP_CALLBACK,
                provider="http",
                target={"connection": "callback"},
                payload_template={"ok": True},
            ),
        ]

        assert router.queue_for_batch(side_effects) == "side_effects.default"
