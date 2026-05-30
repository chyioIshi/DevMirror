"""Mapper between request log verification contracts and domain models."""

from app.api.contracts.request_logs import (
    VerifyRequestLogRequest,
    VerifyRequestLogResponse,
)
from app.domain.request_logs.models.verification import (
    RequestLogVerificationExpectation,
    RequestLogVerificationResult,
)


class RequestLogVerificationContractMapper:
    """Converts request DTOs and request log verification results."""

    @staticmethod
    def to_domain_request_log_verification_model(
        request: VerifyRequestLogRequest,
    ) -> RequestLogVerificationExpectation:
        """Converts a verification request DTO to a domain expectation model.

        Args:
            request: API request DTO with verification criteria.

        Returns:
            Domain expectation model for request log verification.
        """
        return RequestLogVerificationExpectation(
            path=request.path,
            method=request.method,
            expected_count=request.expected_count,
            matched_mock_id=request.matched_mock_id,
        )

    @staticmethod
    def from_domain_request_log_verification_model(
        result: RequestLogVerificationResult,
    ) -> VerifyRequestLogResponse:
        """Converts a domain verification result to a response DTO.

        Args:
            result: Domain request log verification result.

        Returns:
            API response DTO with verification outcome.
        """
        return VerifyRequestLogResponse(
            matched=result.matched,
            actual_count=result.actual_count,
        )
