"""Validation helpers for infrastructure side effect providers."""

from typing import Any

from app.infra.exceptions import InvalidSideEffectProviderConfigError


class SideEffectProviderValidation:
    """Common validation helpers for infrastructure side effect providers."""

    @classmethod
    def optional_string(
        cls,
        mapping: dict[str, Any],
        key: str,
        *,
        subject: str,
    ) -> str | None:
        """Returns a non-empty string value or None when it is absent."""
        value = mapping.get(key)
        if value is None:
            return None
        if isinstance(value, str) and value.strip():
            return value
        raise InvalidSideEffectProviderConfigError(
            f"{subject} {key} must be a non-empty string",
            details={"field": key},
        )

    @classmethod
    def optional_positive_int(
        cls,
        mapping: dict[str, Any],
        key: str,
        field: str,
        *,
        subject: str,
    ) -> int | None:
        """Returns an optional positive integer value."""
        value = mapping.get(key)
        if value is None:
            return None
        if isinstance(value, int) and not isinstance(value, bool) and value > 0:
            return value
        raise InvalidSideEffectProviderConfigError(
            f"{subject} {field} must be a positive integer",
            details={"field": field},
        )

    @classmethod
    def optional_positive_number(
        cls,
        mapping: dict[str, Any],
        key: str,
        field: str,
        *,
        subject: str,
    ) -> float | None:
        """Returns an optional positive int/float value as float."""
        value = mapping.get(key)
        if value is None:
            return None
        if isinstance(value, int | float) and not isinstance(value, bool) and value > 0:
            return float(value)
        raise InvalidSideEffectProviderConfigError(
            f"{subject} {field} must be a positive number",
            details={"field": field},
        )

    @classmethod
    def optional_non_negative_int(
        cls,
        mapping: dict[str, Any],
        key: str,
        field: str,
        *,
        subject: str,
    ) -> int | None:
        """Returns an optional non-negative integer value."""
        value = mapping.get(key)
        if value is None:
            return None
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            return value
        raise InvalidSideEffectProviderConfigError(
            f"{subject} {field} must be a non-negative integer",
            details={"field": field},
        )

    @classmethod
    def required_string(
        cls,
        mapping: dict[str, Any],
        key: str,
        field: str,
        *,
        subject: str,
    ) -> str:
        """Returns a required non-empty string value."""
        value = cls.optional_string(mapping, key, subject=subject)
        if value is None:
            raise InvalidSideEffectProviderConfigError(
                f"{subject} {field} must be configured",
                details={"field": field},
            )
        return value

    @classmethod
    def string_mapping(
        cls,
        value: Any,
        field: str,
        *,
        subject: str,
    ) -> dict[str, str]:
        """Returns a dictionary containing only string keys and string values."""
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise InvalidSideEffectProviderConfigError(
                f"{subject} {field} must be a dictionary",
                details={"field": field},
            )

        result: dict[str, str] = {}
        for key, item in value.items():
            if not isinstance(key, str) or not isinstance(item, str):
                raise InvalidSideEffectProviderConfigError(
                    f"{subject} {field} must contain only string values",
                    details={"field": field},
                )
            result[key] = item
        return result
