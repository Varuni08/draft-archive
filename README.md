# Draft Archive

A personal, from-scratch agentic video production pipeline.

## Why this exists

Inspired by studying OpenMontage's architecture (stage-based pipelines, tool
registries, quality gates) but written independently, with zero shared code,
so the IP is 100% owned by you. No AGPL exposure, ever — even if this later
becomes a hosted product.

## Design principles (how this stays clean)

1. **Original code only.** The orchestrator, registry, and pipeline engine
   below are written from scratch. If you ever go back to read OpenMontage's
   source for inspiration, treat it like reading a textbook — take the idea,
   close the tab, write your own version.
2. **Arm's-length tool calls.** External tools (FFmpeg, Piper, Remotion) are
   invoked as independent subprocesses / HTTP calls — never imported as
   libraries whose source you've modified. This is "mere aggregation," which
   sits outside copyleft obligations.
3. **Permissive dependencies only.** Everything wired in by default here is
   MIT/BSD/public-domain licensed:
   - **Piper TTS** — MIT — free offline text-to-speech
   - **Remotion** — MIT core license — React-based video composition
   - **FFmpeg** — LGPL (default build, no `--enable-gpl` components) — final
     render/mux
   - **Archive.org / Wikimedia Commons / NASA** — public domain / CC —
     stock footage & images
   Before adding any new tool, check its license and note it in
   `tools/LICENSES.md`.

## Architecture

```
Draft Archive/
├── orchestrator/
│   ├── pipeline_engine.py   # loads a pipeline YAML, runs stages in order
│   ├── tool_registry.py     # self-describing tool registration + lookup
│   └── models.py            # dataclasses: Stage, ToolSpec, RunContext
├── tools/                   # each tool = one subprocess/API wrapper
│   ├── tts_piper.py
│   ├── footage_fetch.py
│   ├── render_remotion.py
│   ├── ffmpeg_utils.py
│   └── LICENSES.md
├── pipelines/
│   └── documentary.yaml     # first pipeline: research -> script -> voice -> assets -> compose -> render
├── skills/                  # plain-language notes on how/when to use each tool (your own words)
└── schemas/                 # JSON schema for pipeline validation
```

## Stage flow (documentary pipeline, v1)

1. `research` — gather source material (manual input or web search, your own code)
2. `script` — turn research into a narration script (LLM call, your own prompt)
3. `voice` — Piper TTS renders narration to WAV
4. `assets` — fetch free stock footage/images matching scene descriptions
5. `compose` — Remotion assembles narration + assets + captions into a timeline
6. `render` — FFmpeg muxes final MP4
7. `validate` — ffprobe sanity checks (duration, audio levels, resolution)

## Getting started

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
pip install piper-tts
cd remotion-composer && npm install && cd ..
python -m orchestrator.pipeline_engine pipelines/documentary.yaml --topic "city life in the rain"
```

No API keys required for the default path.
