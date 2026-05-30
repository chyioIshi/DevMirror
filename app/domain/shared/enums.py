"""Enums used by domain models."""

from enum import StrEnum


class HttpMethod(StrEnum):
    """HTTP methods supported by mocks."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    OPTIONS = "OPTIONS"
    HEAD = "HEAD"


class MatchSource(StrEnum):
    """Request data sources available for matching rules."""

    HEADER = "header"
    QUERY = "query"
    PATH = "path"
    BODY_JSON = "body_json"


class MatchOperator(StrEnum):
    """Operators available for evaluating rules."""

    EQ = "eq"
    NEQ = "neq"
    CONTAINS = "contains"
    IN = "in"
    EXISTS = "exists"
