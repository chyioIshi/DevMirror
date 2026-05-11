from app.application.commands import UNSET, UpdateMockCommand
from app.domain.mocks.models import MatchRule, MockResponse
from app.domain.shared import HttpMethod


class CommandFactory:
    """Создает команды application layer."""

    def update_mock(
        self,
        *,
        mock_id: str = "000000000000000000000001",
        name: str | object = UNSET,
        description: str | None | object = UNSET,
        path: str | object = UNSET,
        method: HttpMethod | object = UNSET,
        priority: int | object = UNSET,
        active: bool | object = UNSET,
        scope: str | object = UNSET,
        match_rules: list[MatchRule] | object = UNSET,
        response: MockResponse | object = UNSET,
        tags: list[str] | object = UNSET,
    ) -> UpdateMockCommand:
        """Создает UpdateMockCommand с указанными полями или значениями по умолчанию."""
        
        return UpdateMockCommand(
            mock_id=mock_id,
            name=name,
            description=description,
            path=path,
            method=method,
            priority=priority,
            active=active,
            scope=scope,
            match_rules=match_rules,
            response=response,
            tags=tags,
        )
