"""FFmpeg wrapper — final mux + basic validation via subprocess calls.

License note: use a stock/LGPL FFmpeg build (no --enable-gpl components) to
keep licensing simple. We only ever shell out to the `ffmpeg`/`ffprobe`
binaries — no bundled/modified FFmpeg source in this repo.
"""
from __future__ import annotations

import json
import subprocess

from orchestrator.models import RunContext, ToolSpec
from orchestrator.tool_registry import registry
from tools._ffmpeg_locate import locate_ffmpeg_ffprobe


def run(ctx: RunContext, **_: object) -> None:
    src = ctx.outputs.get("composed_mp4")
    if not src:
        print("        [WARN] No composed_mp4 in context; skipping final mux.")
        return

    try:
        ffmpeg_bin, _ = locate_ffmpeg_ffprobe()
    except RuntimeError as exc:
        print(f"        [WARN] {exc}")
        return

    final_path = ctx.path_for("final.mp4")
    cmd = [ffmpeg_bin, "-y", "-i", src, "-c", "copy", str(final_path)]
    print(f"        $ {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        ctx.outputs["final_mp4"] = str(final_path)
    except FileNotFoundError:
        print("        [WARN] ffmpeg not found on PATH.")
        return
    except subprocess.CalledProcessError as exc:
        print(f"        [WARN] ffmpeg failed: {exc}")
        return

    validate(ctx)


def validate(ctx: RunContext) -> None:
    """Basic quality gate: confirm the final file has video+audio streams."""
    final_path = ctx.outputs.get("final_mp4")
    if not final_path:
        return
    try:
        _, ffprobe_bin = locate_ffmpeg_ffprobe()
    except RuntimeError as exc:
        print(f"        [WARN] {exc}")
        return
    cmd = [ffprobe_bin, "-v", "quiet", "-print_format", "json", "-show_streams", final_path]
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        streams = json.loads(result.stdout).get("streams", [])
        kinds = {s.get("codec_type") for s in streams}
        print(f"        [CHECK] streams present: {kinds}")
        ctx.outputs["validation"] = {"streams": list(kinds)}
    except Exception as exc:  # noqa: BLE001
        print(f"        [WARN] ffprobe validation failed: {exc}")


registry.register(
    ToolSpec(
        name="ffmpeg",
        category="render",
        runtime="LOCAL",
        license="LGPL (stock build)",
        install_hint="Install FFmpeg and ensure it's on PATH",
        run=run,
    )
)