from datetime import UTC, datetime
from uuid import UUID

import pytest

from app.domain.mocks import InvalidSideEffectError
from app.domain.mocks.models import MockResponse, SideEffectContext, SideEffectType
from app.domain.request_contexts import RequestContext
from app.domain.shared import HttpMethod


class TestSideEffectContext:
    """Checks side effect context behavior."""

    def test_context_uses_plain_mapping_without_framework_objects(self) -> None:
        context = SideEffectContext(
            request={"body": {"itemId": "item-1"}},
            mock={"id": "mock-1"},
            response={"status_code": 200},
            execution={"request_id": "request-1"},
        )

        mapping = context.to_mapping()

        assert mapping["request"]["body"]["itemId"] == "item-1"
        assert set(mapping) == {"request", "mock", "response", "execution"}

    def test_from_domain_maps_query_and_normalized_headers(self, mock_factory) -> None:
        request = RequestContext(
            id="request-1",
            method=HttpMethod.POST,
            path="/items",
            headers={"A-CustomerId": "123", "X-Request-ID": "request-1"},
            query_params={"customerId": "query-customer-1"},
            body={"dealId": "deal-1"},
            timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        )
        mock = mock_factory.create_mock(
            mock_id="mock-1",
            method=HttpMethod.POST,
            path="/items",
            response=MockResponse(status_code=201, body={"ok": True}),
        )

        context = SideEffectContext.from_domain(
            request=request,
            mock=mock,
            response=mock.response,
            execution={"request_id": "request-1"},
        )

        assert context.request["headers"] == {
            "a-customerid": "123",
            "x-request-id": "request-1",
        }
        assert context.request["query"] == {"customerId": "query-customer-1"}
        assert "query_params" not in context.request

    def test_from_domain_converts_uuid_str_enum_datetime_and_tuple(
        self,
        mock_factory,
    ) -> None:
        request_uuid = UUID("550e8400-e29b-41d4-a716-446655440000")
        request = RequestContext(
            id=request_uuid,
            method=HttpMethod.POST,
            path="/items",
            timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        )
        mock = mock_factory.create_mock(
            mock_id="mock-1",
            method=HttpMethod.POST,
            path="/items",
            response=MockResponse(status_code=201),
        )

        context = SideEffectContext.from_domain(
            request=request,
            mock=mock,
            response=mock.response,
            execution={
                "request_id": request_uuid,
                "side_effect_type": SideEffectType.MESSAGE_PUBLISH,
                "attempts": (1, 2),
            },
        )

        assert context.request["id"] == "550e8400-e29b-41d4-a716-446655440000"
        assert context.request["method"] == "POST"
        assert context.request["timestamp"] == "2026-01-01T00:00:00+00:00"
        assert context.mock["method"] == "POST"
        assert context.execution == {
            "request_id": "550e8400-e29b-41d4-a716-446655440000",
            "side_effect_type": "message_publish",
            "attempts": [1, 2],
        }

    def test_from_domain_rejects_unsupported_execution_object(self, mock_factory) -> None:
        request = RequestContext(method=HttpMethod.POST, path="/items")
        mock = mock_factory.create_mock(
            method=HttpMethod.POST,
            path="/items",
            response=MockResponse(status_code=201),
        )

        with pytest.raises(InvalidSideEffectError) as exc_info:
            SideEffectContext.from_domain(
                request=request,
                mock=mock,
                response=mock.response,
                execution={"raw": object()},
            )

        assert exc_info.value.details == {"value_type": "object"}
