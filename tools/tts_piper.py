"""Piper TTS wrapper — calls the `piper` CLI as a subprocess.

License note: Piper is MIT-licensed. We never import its internals; we shell
out to the installed `piper` executable, which keeps this file entirely our
own original code regardless of what Piper does internally.

Install: pip install piper-tts
Docs: https://github.com/rhasspy/piper
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from orchestrator.models import RunContext, ToolSpec
from orchestrator.tool_registry import registry


VOICES_DIR = Path.home() / ".local" / "share" / "piper" / "voices"


def _ensure_voice_downloaded(voice: str) -> None:
    """Piper needs each voice model downloaded once before use. Do that
    automatically instead of making the person run a separate command."""
    try:
        from piper.download_voices import download_voice
        VOICES_DIR.mkdir(parents=True, exist_ok=True)
        download_voice(voice, VOICES_DIR)
    except Exception as exc:  # noqa: BLE001
        print(f"        [WARN] Could not auto-download voice '{voice}': {exc}")


def run(ctx: RunContext, text: str | None = None, voice: str = "en_US-lessac-medium") -> None:
    text = text or ctx.outputs.get("script", ctx.topic)
    out_wav = ctx.path_for("narration.wav")

    cmd = [
        "piper",
        "--model", voice,
        "--data_dir", str(VOICES_DIR),
        "--output_file", str(out_wav),
    ]
    print(f"        $ echo <script> | {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, input=text.encode("utf-8"), capture_output=True)
        if result.returncode != 0 and b"Unable to find voice" in result.stderr:
            print(f"        Voice '{voice}' not downloaded yet — fetching it once (free, local)...")
            _ensure_voice_downloaded(voice)
            result = subprocess.run(cmd, input=text.encode("utf-8"), capture_output=True)
        if result.returncode != 0:
            print(f"        [WARN] piper failed: {result.stderr.decode(errors='replace')}")
            return
        ctx.outputs["narration_wav"] = str(out_wav)
    except FileNotFoundError:
        print("        [WARN] `piper` executable not found on PATH. "
              "Run `pip install piper-tts` and ensure it's on PATH.")


registry.register(
    ToolSpec(
        name="piper",
        category="tts",
        runtime="LOCAL",
        license="MIT",
        install_hint="pip install piper-tts",
        run=run,
    )
)