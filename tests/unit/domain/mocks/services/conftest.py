import pytest

from app.domain.mocks.models import SideEffectContext
from app.domain.mocks.services import SideEffectTemplateRenderer


@pytest.fixture
def side_effect_context() -> SideEffectContext:
    return SideEffectContext(
        request={
            "body": {
                "dealId": "deal-1",
                "items": [{"id": "item-1"}],
            },
            "headers": {"a-customerid": "customer-1"},
            "query": {"customerId": "query-customer-1"},
        },
        mock={"id": "mock-1"},
        response={"status_code": 202},
        execution={"request_id": "request-1"},
    )


@pytest.fixture
def side_effect_template_renderer() -> SideEffectTemplateRenderer:
    return SideEffectTemplateRenderer()
