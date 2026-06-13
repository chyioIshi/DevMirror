import pytest

from app.domain.mocks import InvalidSideEffectError
from app.domain.mocks.models import (
    SideEffect,
    SideEffectFailPolicy,
    SideEffectMode,
    SideEffectType,
)


class TestSideEffect:
    """Checks side effect value object defaults and validation."""

    def test_applies_defaults(self) -> None:
        side_effect = SideEffect(
            type=SideEffectType.MESSAGE_PUBLISH,
            provider="kafka",
            target={"topic": "user-events"},
            payload_template={"user_id": "{{body.id}}"},
        )

        assert side_effect.options == {}
        assert side_effect.mode == SideEffectMode.ASYNC
        assert side_effect.fail_policy == SideEffectFailPolicy.IGNORE
        assert side_effect.enabled is True

    def test_rejects_blank_provider(self) -> None:
        with pytest.raises(InvalidSideEffectError):
            SideEffect(
                type=SideEffectType.MESSAGE_PUBLISH,
                provider=" ",
                target={"topic": "user-events"},
                payload_template={"ok": True},
            )

    def test_message_publish_allows_queue_target(self) -> None:
        side_effect = SideEffect(
            type=SideEffectType.MESSAGE_PUBLISH,
            provider="rabbit",
            target={"queue": "user-events"},
            payload_template={"ok": True},
        )

        assert side_effect.target == {"queue": "user-events"}

    @pytest.mark.parametrize("target", [{}, {"topic": " "}, {"queue": ""}, {"topic": 123}])
    def test_message_publish_requires_topic_or_queue(self, target: dict[str, object]) -> None:
        with pytest.raises(InvalidSideEffectError):
            SideEffect(
                type=SideEffectType.MESSAGE_PUBLISH,
                provider="kafka",
                target=target,
                payload_template={"ok": True},
            )

    @pytest.mark.parametrize("type_", [SideEffectType.DB_INSERT, SideEffectType.DB_UPDATE])
    @pytest.mark.parametrize("target", [{"table": "users"}, {"collection": "users"}])
    def test_db_side_effects_allow_table_or_collection_target(
        self,
        type_: SideEffectType,
        target: dict[str, str],
    ) -> None:
        side_effect = SideEffect(
            type=type_,
            provider="mongo",
            target=target,
            payload_template={"ok": True},
        )

        assert side_effect.target == target

    @pytest.mark.parametrize("type_", [SideEffectType.DB_INSERT, SideEffectType.DB_UPDATE])
    @pytest.mark.parametrize("target", [{}, {"table": " "}, {"collection": ""}, {"table": 123}])
    def test_db_side_effects_require_table_or_collection_target(
        self,
        type_: SideEffectType,
        target: dict[str, object],
    ) -> None:
        with pytest.raises(InvalidSideEffectError):
            SideEffect(
                type=type_,
                provider="mongo",
                target=target,
                payload_template={"ok": True},
            )

    def test_http_callback_requires_connection_target(
        self,
    ) -> None:
        side_effect = SideEffect(
            type=SideEffectType.HTTP_CALLBACK,
            provider="http",
            target={"connection": "main-http"},
            payload_template={"ok": True},
        )

        assert side_effect.target == {"connection": "main-http"}

    @pytest.mark.parametrize(
        "target",
        [{}, {"url": "https://example.test/callback"}, {"connection": ""}, {"connection": 123}],
    )
    def test_http_callback_rejects_missing_connection_target(
        self,
        target: dict[str, object],
    ) -> None:
        with pytest.raises(InvalidSideEffectError):
            SideEffect(
                type=SideEffectType.HTTP_CALLBACK,
                provider="http",
                target=target,
                payload_template={"ok": True},
            )

    def test_retry_fail_policy_requires_max_attempts(self) -> None:
        with pytest.raises(InvalidSideEffectError):
            SideEffect(
                type=SideEffectType.HTTP_CALLBACK,
                provider="http",
                target={"connection": "main-http"},
                payload_template={"ok": True},
                fail_policy=SideEffectFailPolicy.RETRY,
            )

    @pytest.mark.parametrize("max_attempts", [0, -1, True, "3"])
    def test_retry_fail_policy_rejects_invalid_max_attempts(self, max_attempts: object) -> None:
        with pytest.raises(InvalidSideEffectError):
            SideEffect(
                type=SideEffectType.HTTP_CALLBACK,
                provider="http",
                target={"connection": "main-http"},
                payload_template={"ok": True},
                options={"max_attempts": max_attempts},
                fail_policy=SideEffectFailPolicy.RETRY,
            )
