from enum import StrEnum


class HttpMethod(StrEnum):
    """Перечисляет HTTP-методы, поддерживаемые моками."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    OPTIONS = "OPTIONS"
    HEAD = "HEAD"


class MatchSource(StrEnum):
    """Перечисляет источники данных запроса для сопоставления правил."""

    HEADER = "header"
    QUERY = "query"
    PATH = "path"
    BODY_JSON = "body_json"


class MatchOperator(StrEnum):
    """Перечисляет операторы, доступные для вычисления правил."""

    EQ = "eq"
    NEQ = "neq"
    CONTAINS = "contains"
    IN = "in"
    EXISTS = "exists"
