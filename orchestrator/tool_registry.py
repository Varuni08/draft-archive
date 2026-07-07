"""Tool registry: tools register themselves, the engine picks by category.

This is written independently — the pattern (self-describing tools looked up
by category/runtime availability) is a common architecture idea, not
copyrightable expression, so it's safe to reimplement from your own
understanding.
"""
from __future__ import annotations

import os
from typing import Optional

from orchestrator.models import ToolSpec


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, list[ToolSpec]] = {}

    def register(self, tool: ToolSpec) -> None:
        self._tools.setdefault(tool.category, []).append(tool)

    def available(self, category: str) -> list[ToolSpec]:
        env = dict(os.environ)
        return [t for t in self._tools.get(category, []) if t.is_available(env)]

    def pick(self, category: str, prefer_free: bool = True) -> Optional[ToolSpec]:
        """Pick the best available tool for a category.

        Default policy: prefer FREE/LOCAL runtimes over API ones, so the
        pipeline runs at zero cost unless you explicitly configure a paid
        tool and set prefer_free=False.
        """
        options = self.available(category)
        if not options:
            return None
        if prefer_free:
            free = [t for t in options if t.runtime in ("FREE", "LOCAL")]
            if free:
                return free[0]
        return options[0]

    def status_report(self) -> str:
        lines = []
        for category, tools in self._tools.items():
            env = dict(os.environ)
            ok = [t for t in tools if t.is_available(env)]
            lines.append(f"{category}: {len(ok)}/{len(tools)} configured")
            for t in tools:
                mark = "x" if t.is_available(env) else " "
                lines.append(f"  [{mark}] {t.name} ({t.runtime}, {t.license})")
        return "\n".join(lines)


# Global registry instance, populated by tools/*.py on import
registry = ToolRegistry()
