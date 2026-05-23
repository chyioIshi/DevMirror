from app.api.contracts.request_logs import VerifyRequestLogRequest
from app.api.mappers.request_log_verification_contract_mapper import (
    RequestLogVerificationContractMapper,
)
from app.domain.request_logs.models.verification import RequestLogVerificationResult
from app.domain.shared import HttpMethod


class TestRequestLogVerificationContractMapper:
    """Проверяет маппинг request log verification dto в domain model и обратно."""

    def test_to_domain_maps_request_dto(self) -> None:
        """Проверяет маппинг API dto в domain model."""
        request = VerifyRequestLogRequest(
            path="/users",
            method=HttpMethod.POST,
            expected_count=2,
            matched_mock_id="mock-1",
        )

        expectation = RequestLogVerificationContractMapper.to_domain_request_log_verification_model(
            request
        )

        assert expectation.path == "/users"
        assert expectation.method == HttpMethod.POST
        assert expectation.expected_count == 2
        assert expectation.matched_mock_id == "mock-1"

    def test_from_domain_maps_result(self) -> None:
        """Проверяет маппинг domain model в API dto."""
        result = RequestLogVerificationResult(matched=True, actual_count=3)

        response = RequestLogVerificationContractMapper.from_domain_request_log_verification_model(
            result
        )

        assert response.matched is True
        assert response.actual_count == 3
