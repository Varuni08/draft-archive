"""Pipeline engine: loads a YAML manifest, runs each stage in order.

Usage:
    python -m orchestrator.pipeline_engine pipelines/documentary.yaml --topic "city life in the rain"
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

# Load .env before anything else touches os.environ, so tool availability
# checks (e.g. GROQ_API_KEY) see it. encoding="utf-8-sig" strips a Windows
# BOM if Notepad/PowerShell added one when the file was saved.
load_dotenv(encoding="utf-8-sig")

# Extra safety learned the hard way on Windows: strip stray \r / whitespace
# that a BOM-unaware editor can leave on a value, which otherwise makes the
# key silently invalid (e.g. "Invalid Deepgram API key" - same failure mode
# would show up here as a Groq 401).
for _key in ("GROQ_API_KEY",):
    if _key in os.environ:
        os.environ[_key] = os.environ[_key].strip()

# Ensure tools register themselves with the global registry on import
import tools.script_writer  # noqa: F401
import tools.tts_piper  # noqa: F401
import tools.align_whisper  # noqa: F401
import tools.footage_fetch  # noqa: F401
import tools.render_remotion  # noqa: F401
import tools.ffmpeg_utils  # noqa: F401

from orchestrator.models import RunContext, Stage
from orchestrator.tool_registry import registry


def load_pipeline(path: Path) -> list[Stage]:
    data = yaml.safe_load(path.read_text())
    stages = []
    for raw in data.get("stages", []):
        stages.append(
            Stage(
                name=raw["name"],
                tool_category=raw["tool_category"],
                params=raw.get("params", {}),
            )
        )
    return stages


def run_pipeline(pipeline_path: Path, topic: str, work_dir: Path) -> RunContext:
    stages = load_pipeline(pipeline_path)
    ctx = RunContext(topic=topic, work_dir=work_dir)

    print(f"Draft Archive — running '{pipeline_path.stem}' pipeline for topic: {topic!r}")
    print(registry.status_report())
    print("-" * 60)

    for stage in stages:
        params = dict(stage.params)
        prefer_free = params.pop("prefer_free", True)
        tool = registry.pick(stage.tool_category, prefer_free=prefer_free)
        if tool is None:
            print(f"[SKIP] Stage '{stage.name}': no tool available for "
                  f"category '{stage.tool_category}'")
            continue
        print(f"[RUN ] Stage '{stage.name}' -> tool '{tool.name}' ({tool.runtime})")
        if tool.run is None:
            print(f"        (stub: {tool.name} has no run() implemented yet)")
            continue
        tool.run(ctx, **params)

    print("-" * 60)
    print("Pipeline finished. Outputs:")
    for key, value in ctx.outputs.items():
        print(f"  {key}: {value}")
    return ctx


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a Draft Archive pipeline")
    parser.add_argument("pipeline", type=Path, help="Path to pipeline YAML")
    parser.add_argument("--topic", required=True, help="Video topic / prompt")
    parser.add_argument("--work-dir", type=Path, default=Path("./_work"))
    args = parser.parse_args()

    run_pipeline(args.pipeline, args.topic, args.work_dir)


if __name__ == "__main__":
    sys.exit(main())
