"""Core data models for the Draft Archive pipeline engine.

Written from scratch: dataclasses describing a pipeline stage, a tool's
self-declared capability, and the shared run context passed between stages.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional


@dataclass
class ToolSpec:
    """A self-describing wrapper around one external tool.

    `runtime` distinguishes tools that need nothing (FREE), a local install
    (LOCAL), or a paid API key (API) — mirrors the "X of Y configured"
    visibility pattern, but implemented independently here.
    """

    name: str
    category: str  # e.g. "tts", "footage", "compose", "render"
    runtime: str  # "FREE" | "LOCAL" | "API"
    license: str  # e.g. "MIT", "LGPL", "public-domain"
    requires_env: list[str] = field(default_factory=list)
    run: Optional[Callable[..., Any]] = None
    install_hint: str = ""

    def is_available(self, env: dict[str, str]) -> bool:
        if self.runtime == "FREE" or self.runtime == "LOCAL":
            return True
        return all(env.get(key) for key in self.requires_env)


@dataclass
class Stage:
    name: str
    tool_category: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class RunContext:
    """Carries state between stages: paths, chosen topic, intermediate files."""

    topic: str
    work_dir: Path
    outputs: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Always store an absolute path. Several tools (e.g. Remotion) run
        # as a subprocess with a *different* working directory, so a
        # relative "_work/foo.json" would silently resolve to the wrong
        # place once that subprocess's cwd changes.
        self.work_dir = Path(self.work_dir).resolve()

    def path_for(self, name: str) -> Path:
        self.work_dir.mkdir(parents=True, exist_ok=True)
        return self.work_dir / name