
from app.api.contracts.request_logs import VerifyRequestLogRequest, VerifyRequestLogResponse
from app.domain.request_logs.models.verification import (
    RequestLogVerificationExpectation,
    RequestLogVerificationResult,
)


class RequestLogVerificationContractMapper:
    """Преобразует REQUEST DTO и результат проверки журнала запросов."""

    @staticmethod
    def to_domain_request_log_verification_model(
        request: VerifyRequestLogRequest,
    ) -> RequestLogVerificationExpectation:
        """Преобразует REQUEST DTO запроса проверки в доменную модель ожиданий."""
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
        """Преобразует доменный результат проверки в RESPONSE DTO ответа."""
        return VerifyRequestLogResponse(
            matched=result.matched,
            actual_count=result.actual_count,
        )
