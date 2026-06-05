import pytest
from pydantic import ValidationError

from app.api.contracts.mocks.items import MockResponsePayloadItem, SideEffectItem
from app.domain.mocks.models import SideEffectFailPolicy, SideEffectMode, SideEffectType


class TestMockResponsePayloadItem:
    """Checks mock response payload contract defaults and validation."""

    def test_defaults_to_no_side_effects(self) -> None:
        response = MockResponsePayloadItem(status_code=200)

        assert response.side_effects == []

    def test_side_effect_applies_defaults(self) -> None:
        side_effect = SideEffectItem(
            type="message_publish",
            provider="kafka",
            target={"topic": "events"},
            payload_template={"ok": True},
        )

        assert side_effect.type == SideEffectType.MESSAGE_PUBLISH
        assert side_effect.options == {}
        assert side_effect.mode == SideEffectMode.ASYNC
        assert side_effect.fail_policy == SideEffectFailPolicy.IGNORE
        assert side_effect.enabled is True

    @pytest.mark.parametrize(
        ("field_name", "value"),
        [
            ("type", "unknown"),
            ("mode", "later"),
            ("fail_policy", "stop"),
        ],
    )
    def test_side_effect_rejects_invalid_enum_values(
        self,
        field_name: str,
        value: str,
    ) -> None:
        payload = {
            "type": "message_publish",
            "provider": "kafka",
            "target": {"topic": "events"},
            "payload_template": {"ok": True},
        }
        payload[field_name] = value

        with pytest.raises(ValidationError):
            SideEffectItem(**payload)
