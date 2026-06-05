"""Template rendering for side effect payloads and options."""

import re
from typing import Any

from app.domain.mocks.exceptions import SideEffectTemplateRenderError
from app.domain.mocks.models import SideEffect, SideEffectContext

_PLACEHOLDER_PATTERN = re.compile(r"{{\s*([A-Za-z_][A-Za-z0-9_-]*(?:\.[A-Za-z0-9_-]+)*)\s*}}")


class SideEffectTemplateRenderer:
    """Renders side effect templates using a plain side effect context.

    Placeholders are supported in dictionary values, list items, and strings.
    Dictionary keys are not rendered as templates for now.
    """

    def render_payload(
        self,
        side_effect: SideEffect,
        context: SideEffectContext,
    ) -> dict[str, Any]:
        """Renders a side effect payload template."""
        return self.render(side_effect.payload_template, context)

    def render_options(
        self,
        side_effect: SideEffect,
        context: SideEffectContext,
    ) -> dict[str, Any]:
        """Renders a side effect options template."""
        return self.render(side_effect.options, context)

    def render(self, template: Any, context: SideEffectContext) -> Any:
        """Renders placeholders in nested dictionaries, lists, and strings."""
        if isinstance(template, dict):
            return {key: self.render(value, context) for key, value in template.items()}
        if isinstance(template, list):
            return [self.render(value, context) for value in template]
        if isinstance(template, str):
            return self._render_string(template, context)
        return template

    def _render_string(self, template: str, context: SideEffectContext) -> Any:
        match = _PLACEHOLDER_PATTERN.fullmatch(template)
        if match:
            return self._resolve(match.group(1), context)

        return _PLACEHOLDER_PATTERN.sub(
            lambda match_: str(self._resolve(match_.group(1), context)),
            template,
        )

    def _resolve(self, path: str, context: SideEffectContext) -> Any:
        current: Any = context.to_mapping()
        for segment in path.split("."):
            if isinstance(current, dict) and segment in current:
                current = current[segment]
                continue
            if isinstance(current, list) and segment.isdigit():
                index = int(segment)
                if 0 <= index < len(current):
                    current = current[index]
                    continue
            raise SideEffectTemplateRenderError(
                "Side effect template placeholder could not be resolved",
                details={"path": path, "missing_segment": segment},
            )
        return current
