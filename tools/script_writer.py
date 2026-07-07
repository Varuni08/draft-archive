"""Script writer — turns a topic into a narration script.

Two tools registered here:

  - `template_script` (FREE, no key needed): a simple, rule-based script
    builder. Always available, so the pipeline never gets stuck at zero
    cost. Quality is basic — three-beat structure (hook / body / close).

  - `groq_script` (API, needs GROQ_API_KEY): calls Groq's OpenAI-compatible
    chat completions endpoint for a real LLM-written script. Groq's free
    tier is generous and fast — good fit if you want better scripts without
    spending money. Get a free key at https://console.groq.com.

Both are original code — plain HTTP via urllib for Groq, no vendored SDK.
"""
from __future__ import annotations

import json
import os
import urllib.request

from orchestrator.models import RunContext, ToolSpec
from orchestrator.tool_registry import registry

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"


def _write_script_file(ctx: RunContext, text: str) -> None:
    script_path = ctx.path_for("script.txt")
    script_path.write_text(text)
    ctx.outputs["script"] = text
    ctx.outputs["script_path"] = str(script_path)


def run_template(ctx: RunContext, tone: str = "documentary") -> None:
    topic = ctx.topic
    text = (
        f"[HOOK]\n"
        f"There's something worth pausing on about {topic}.\n\n"
        f"[BODY]\n"
        f"Consider {topic} — the details often go unnoticed, but they shape "
        f"the moment more than we realize.\n\n"
        f"[CLOSE]\n"
        f"And that's {topic}, seen a little closer.\n"
    )
    print("        (template script — set GROQ_API_KEY for a real LLM script)")
    _write_script_file(ctx, text)


def run_groq(ctx: RunContext, tone: str = "documentary", max_words: int = 150) -> None:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("        [WARN] GROQ_API_KEY not set — falling back to template.")
        return run_template(ctx, tone=tone)

    prompt = (
        f"Write a {tone}-style narration script about: {ctx.topic}. "
        f"Keep it under {max_words} words. Plain prose, no stage directions, "
        f"no headers — just the narration text a voice actor would read."
    )
    body = json.dumps({
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
    }).encode("utf-8")

    req = urllib.request.Request(
        GROQ_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = data["choices"][0]["message"]["content"].strip()
        _write_script_file(ctx, text)
    except Exception as exc:  # noqa: BLE001
        print(f"        [WARN] Groq call failed ({exc}); falling back to template.")
        run_template(ctx, tone=tone)


registry.register(
    ToolSpec(
        name="template_script",
        category="script",
        runtime="FREE",
        license="n/a (local logic)",
        run=run_template,
    )
)

registry.register(
    ToolSpec(
        name="groq_script",
        category="script",
        runtime="API",
        license="Groq API (free tier available)",
        requires_env=["GROQ_API_KEY"],
        install_hint="Get a free key at https://console.groq.com and set GROQ_API_KEY",
        run=run_groq,
    )
)
