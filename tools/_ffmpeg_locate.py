"""Locate ffmpeg/ffprobe without requiring a manual system install.

Tries the system PATH first (if you already have FFmpeg installed, this
costs nothing extra). If not found, falls back to `static-ffmpeg`, which
downloads free static binaries once (from a public GitHub release, no
account/key needed) and caches them — so a broke/rushed Windows setup still
works without fighting PATH configuration.

Install: pip install static-ffmpeg
"""
from __future__ import annotations

import shutil


def locate_ffmpeg_ffprobe() -> tuple[str, str]:
    system_ffmpeg = shutil.which("ffmpeg")
    system_ffprobe = shutil.which("ffprobe")
    if system_ffmpeg and system_ffprobe:
        return system_ffmpeg, system_ffprobe

    try:
        from static_ffmpeg import run
        return run.get_or_fetch_platform_executables_else_raise()
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            "Could not find ffmpeg/ffprobe on PATH, and the static-ffmpeg "
            "fallback failed too. Run `pip install static-ffmpeg`, or "
            f"install FFmpeg manually and add it to PATH. ({exc})"
        ) from exc
