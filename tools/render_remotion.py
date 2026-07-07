"""Remotion composer wrapper — invokes the Remotion CLI as a subprocess.

License note: Remotion's core is MIT-licensed. We shell out to `npx remotion
render` against our own React composition project (remotion-composer/,
written by us) — we never copy Remotion's own source or another project's
composition components.

Design note: this tool reads the asset manifest / captions JSON and probes
the narration's real duration itself, then hands Remotion one fully-resolved
props blob. The composition never reads files off disk on its own — that
sidesteps a real Remotion/webpack bundling quirk where importing "fs" inside
a file that's also bundled for the browser preview fails to resolve.

Setup (one-time):
    cd remotion-composer && npm install
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path

from orchestrator.models import RunContext, ToolSpec
from orchestrator.tool_registry import registry
from tools._ffmpeg_locate import locate_ffmpeg_ffprobe

COMPOSER_DIR = Path(__file__).resolve().parent.parent / "remotion-composer"


def _probe_audio_duration(wav_path: str) -> float:
    """Ask ffprobe how long the narration actually is, in seconds."""
    if not wav_path or not Path(wav_path).exists():
        return 8.0
    try:
        _, ffprobe_bin = locate_ffmpeg_ffprobe()
    except RuntimeError as exc:
        print(f"        [WARN] {exc}; using 8s fallback.")
        return 8.0
    cmd = [ffprobe_bin, "-v", "quiet", "-print_format", "json", "-show_format", wav_path]
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return float(json.loads(result.stdout)["format"]["duration"])
    except Exception as exc:  # noqa: BLE001
        print(f"        [WARN] Could not probe narration duration ({exc}); using 8s fallback.")
        return 8.0


def _load_json(path: str) -> list:
    if not path or not Path(path).exists():
        return []
    try:
        return json.loads(Path(path).read_text())
    except Exception as exc:  # noqa: BLE001
        print(f"        [WARN] Could not read {path}: {exc}")
        return []


def _copy_assets_to_public(assets: list[dict], assets_dir: str) -> list[dict]:
    """Copy each downloaded asset image into public/assets/ so Remotion can
    serve it via staticFile() — same reasoning as the narration audio copy:
    Remotion's Img/Audio components only work with real remote http(s) URLs
    or files already inside the project's public/ folder."""
    if not assets_dir or not Path(assets_dir).exists():
        return []
    public_assets_dir = COMPOSER_DIR / "public" / "assets"
    public_assets_dir.mkdir(parents=True, exist_ok=True)

    resolved = []
    for item in assets:
        filename = item.get("filename", "")
        src = Path(assets_dir) / filename
        if not filename or not src.exists():
            continue
        shutil.copyfile(src, public_assets_dir / filename)
        resolved.append({"title": item.get("title", ""), "staticPath": f"assets/{filename}"})
    return resolved


def run(ctx: RunContext, composition_id: str = "Documentary", show_captions: bool = True) -> None:
    narration_path = ctx.outputs.get("narration_wav", "")
    raw_assets = _load_json(ctx.outputs.get("asset_manifest", ""))
    assets = _copy_assets_to_public(raw_assets, ctx.outputs.get("assets_dir", ""))
    captions = _load_json(ctx.outputs.get("captions_json", ""))
    audio_duration = _probe_audio_duration(narration_path)

    # Remotion's Audio/Img components only accept genuine http(s) URLs or
    # files served from the project's own public/ folder (via staticFile())
    # — not arbitrary absolute filesystem paths, even as a well-formed
    # file:// URI. So we copy the narration in and reference it by the
    # relative filename Remotion expects.
    narration_filename = ""
    if narration_path and Path(narration_path).exists():
        public_dir = COMPOSER_DIR / "public"
        public_dir.mkdir(parents=True, exist_ok=True)
        narration_filename = "narration.wav"
        shutil.copyfile(narration_path, public_dir / narration_filename)

    props_path = ctx.path_for("remotion_props.json")
    props = {
        "topic": ctx.topic,
        "narrationPath": narration_filename,  # relative to public/, or "" if none
        "assets": assets,
        "captions": captions,
        "showCaptions": show_captions,
        "audioDurationInSeconds": audio_duration,
    }
    props_path.write_text(json.dumps(props, indent=2))

    out_mp4 = ctx.path_for("composed.mp4")
    cmd = [
        "npx", "remotion", "render",
        composition_id,
        str(out_mp4),
        f"--props={props_path}",
        "--timeout=120000",  # more generous than the 30s default — first
                              # launches can be slow (antivirus scanning the
                              # freshly-downloaded headless Chrome, cloud
                              # sync tools like OneDrive locking files, etc.)
    ]
    print(f"        $ {' '.join(cmd)}  (cwd={COMPOSER_DIR})")

    attempts = 3
    for attempt in range(1, attempts + 1):
        try:
            subprocess.run(
                cmd,
                cwd=COMPOSER_DIR,
                check=True,
                shell=(os.name == "nt"),  # npx is npx.cmd on Windows — needs a shell
            )
            ctx.outputs["composed_mp4"] = str(out_mp4)
            return
        except FileNotFoundError:
            print("        [WARN] npx/remotion not found. Run `cd remotion-composer "
                  "&& npm install` first.")
            return
        except subprocess.CalledProcessError as exc:
            if attempt < attempts:
                wait = 5 * attempt
                print(f"        [WARN] remotion render failed (attempt {attempt}/{attempts}): "
                      f"{exc}. Retrying in {wait}s — this step can be flaky on the first "
                      f"real launch (antivirus scanning the new browser binary, a cloud-sync "
                      f"folder like OneDrive locking files, etc).")
                time.sleep(wait)
            else:
                print(f"        [WARN] remotion render failed after {attempts} attempts: {exc}")
                print("        If this keeps happening: try running from a folder that "
                      "isn't OneDrive/Dropbox-synced, or temporarily pause sync and retest.")


registry.register(
    ToolSpec(
        name="remotion",
        category="compose",
        runtime="LOCAL",
        license="MIT",
        install_hint="cd remotion-composer && npm install",
        run=run,
    )
)