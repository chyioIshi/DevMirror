import pytest

from app.domain.mocks import SideEffectTemplateRenderError
from app.domain.mocks.models import (
    SideEffect,
    SideEffectContext,
    SideEffectType,
)
from app.domain.mocks.services import SideEffectTemplateRenderer


class TestSideEffectTemplateRenderer:
    """Checks side effect payload and option template rendering."""

    def test_renders_nested_dicts(
        self,
        side_effect_context: SideEffectContext,
        side_effect_template_renderer: SideEffectTemplateRenderer,
    ) -> None:
        side_effect = SideEffect(
            type=SideEffectType.MESSAGE_PUBLISH,
            provider="kafka",
            target={"topic": "events"},
            payload_template={
                "deal": {
                    "id": "{{request.body.dealId}}",
                    "customer_id": "{{request.headers.a-customerid}}",
                    "query_customer_id": "{{request.query.customerId}}",
                    "mock_id": "{{mock.id}}",
                    "status_code": "{{response.status_code}}",
                    "request_id": "{{execution.request_id}}",
                },
            },
        )

        result = side_effect_template_renderer.render_payload(side_effect, side_effect_context)

        assert result == {
            "deal": {
                "id": "deal-1",
                "customer_id": "customer-1",
                "query_customer_id": "query-customer-1",
                "mock_id": "mock-1",
                "status_code": 202,
                "request_id": "request-1",
            },
        }

    def test_renders_lists(
        self,
        side_effect_context: SideEffectContext,
        side_effect_template_renderer: SideEffectTemplateRenderer,
    ) -> None:
        template = {
            "items": [
                "{{request.body.dealId}}",
                "{{request.body.items.0.id}}",
                {"status": "{{response.status_code}}"},
                "status={{response.status_code}}",
            ],
        }

        result = side_effect_template_renderer.render(template, side_effect_context)

        assert result == {
            "items": [
                "deal-1",
                "item-1",
                {"status": 202},
                "status=202",
            ],
        }

    def test_renders_options(
        self,
        side_effect_context: SideEffectContext,
        side_effect_template_renderer: SideEffectTemplateRenderer,
    ) -> None:
        side_effect = SideEffect(
            type=SideEffectType.MESSAGE_PUBLISH,
            provider="kafka",
            target={"topic": "events"},
            payload_template={"ok": True},
            options={
                "key": "{{request.body.dealId}}",
                "headers": {"x-request-id": "{{execution.request_id}}"},
            },
        )

        result = side_effect_template_renderer.render_options(side_effect, side_effect_context)

        assert result == {
            "key": "deal-1",
            "headers": {"x-request-id": "request-1"},
        }

    def test_raises_clear_error_for_missing_values(
        self,
        side_effect_context: SideEffectContext,
        side_effect_template_renderer: SideEffectTemplateRenderer,
    ) -> None:
        template = {"record_id": "{{request.body.missing}}"}

        with pytest.raises(SideEffectTemplateRenderError) as exc_info:
            side_effect_template_renderer.render(template, side_effect_context)

        assert exc_info.value.details == {
            "path": "request.body.missing",
            "missing_segment": "missing",
        }

    def test_full_string_placeholder_preserves_original_type(
        self,
        side_effect_context: SideEffectContext,
        side_effect_template_renderer: SideEffectTemplateRenderer,
    ) -> None:
        result = side_effect_template_renderer.render(
            "{{response.status_code}}",
            side_effect_context,
        )

        assert result == 202

    def test_embedded_placeholder_converts_value_to_string(
        self,
        side_effect_context: SideEffectContext,
        side_effect_template_renderer: SideEffectTemplateRenderer,
    ) -> None:
        result = side_effect_template_renderer.render(
            "status={{response.status_code}}",
            side_effect_context,
        )

        assert result == "status=202"
