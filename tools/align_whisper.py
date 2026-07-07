"""Word-level alignment via faster-whisper — free, local, offline, forever.

faster-whisper is a CPU-optimized reimplementation of OpenAI's Whisper model
(MIT-licensed code; the model weights are released under a permissive
license too). It downloads a small model file once, then runs entirely on
your machine — no API key, no account, no per-use cost, no internet call
after the first download.

This gives the Remotion composition real word-level timestamps to sync
captions against, instead of a rough word-count estimate.

Install: pip install faster-whisper
"""
from __future__ import annotations

import json

from orchestrator.models import RunContext, ToolSpec
from orchestrator.tool_registry import registry


def run(ctx: RunContext, model_size: str = "tiny", **_: object) -> None:
    narration_wav = ctx.outputs.get("narration_wav")
    if not narration_wav:
        print("        [WARN] No narration_wav in context; skipping alignment.")
        return

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("        [WARN] faster-whisper not installed. "
              "Run `pip install faster-whisper`.")
        return

    print(f"        Loading Whisper '{model_size}' model (CPU, first run downloads it once)...")
    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    segments, _info = model.transcribe(narration_wav, word_timestamps=True)

    words = []
    for segment in segments:
        for word in segment.words or []:
            words.append({
                "word": word.word.strip(),
                "start": round(word.start, 3),
                "end": round(word.end, 3),
            })

    captions_path = ctx.path_for("captions.json")
    captions_path.write_text(json.dumps(words, indent=2))
    ctx.outputs["captions_json"] = str(captions_path)
    print(f"        Aligned {len(words)} words -> {captions_path}")


registry.register(
    ToolSpec(
        name="whisper_align",
        category="align",
        runtime="LOCAL",
        license="MIT (code) + permissive model weights",
        install_hint="pip install faster-whisper",
        run=run,
    )
)
