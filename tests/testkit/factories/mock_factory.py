from collections.abc import Sequence
from dataclasses import replace
from datetime import datetime
from typing import Any

from app.domain.mocks.models import MatchRule, Mock, MockResponse, SideEffect
from app.domain.shared import HttpMethod, MatchOperator, MatchSource


class MockFactory:
    """Создает объекты Mock."""

    def create_mock(
        self,
        *,
        mock_id: str | None = None,
        name: str = "test-mock",
        path: str = "/test",
        method: HttpMethod = HttpMethod.GET,
        description: str | None = None,
        priority: int = 0,
        active: bool = False,
        scope: str = "global",
        match_rules: Sequence[MatchRule] | None = None,
        match_rules_count: int = 0,
        response: MockResponse | None = None,
        response_status_code: int = 200,
        response_headers: dict[str, str] | None = None,
        response_body: Any | None = None,
        response_side_effects: Sequence[SideEffect] | None = None,
        tags: Sequence[str] | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> Mock:
        """Создает Mock с указанными полями или значениями по умолчанию."""
        rules = (
            list(match_rules) if match_rules is not None else self.match_rules(match_rules_count)
        )
        mock = Mock.create_new(
            name=name,
            path=path,
            method=method,
            description=description,
            priority=priority,
            active=active,
            scope=scope,
            match_rules=rules,
            response=response
            or MockResponse(
                status_code=response_status_code,
                headers=response_headers or {},
                body=response_body,
                side_effects=list(response_side_effects)
                if response_side_effects is not None
                else [],
            ),
            tags=list(tags) if tags is not None else None,
        )

        if mock_id is not None or created_at is not None or updated_at is not None:
            mock = replace(
                mock,
                id=mock_id,
                created_at=created_at or mock.created_at,
                updated_at=updated_at or mock.updated_at,
            )

        return mock

    def match_rule(
        self,
        *,
        source: MatchSource = MatchSource.HEADER,
        key: str = "x-test",
        operator: MatchOperator = MatchOperator.EQ,
        expected: Any = "value",
    ) -> MatchRule:
        """Создает MatchRule со значениями по умолчанию."""
        return MatchRule(source=source, key=key, operator=operator, expected=expected)

    def match_rules(self, count: int) -> list[MatchRule]:
        """Создает список MatchRule с уникальными ключами и значениями."""
        return [
            self.match_rule(key=f"x-test-{index}", expected=f"value-{index}")
            for index in range(count)
        ]
