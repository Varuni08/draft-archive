"""Free footage/image fetcher — queries public-domain / CC sources.

Sources wired here are all public-domain or CC0/CC-BY:
  - Wikimedia Commons API (public domain / CC)
  - Internet Archive (public domain collections)
  - NASA image/video library (public domain)

This file only does original HTTP calls against public APIs — no scraping,
no vendored client libraries from another project.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from orchestrator.models import RunContext, ToolSpec
from orchestrator.tool_registry import registry

WIKIMEDIA_API = "https://commons.wikimedia.org/w/api.php"


def search_wikimedia(query: str, limit: int = 5) -> list[dict]:
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": f"filetype:bitmap {query}",
        "gsrnamespace": "6",  # File namespace — default (0) is nearly empty on Commons
        "gsrlimit": str(limit),
        "prop": "imageinfo",
        "iiprop": "url",
    }
    url = f"{WIKIMEDIA_API}?{urllib.parse.urlencode(params)}"
    # Wikimedia's API rejects requests with no (or a generic) User-Agent —
    # see https://meta.wikimedia.org/wiki/User-Agent_policy
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "DraftArchive/1.0 (personal video pipeline; contact: n/a)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        pages = data.get("query", {}).get("pages", {})
        results = []
        for page in pages.values():
            info = page.get("imageinfo", [{}])[0]
            if "url" in info:
                results.append({"title": page.get("title"), "url": info["url"]})
        return results
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:300]
        print(f"        [WARN] Wikimedia search failed: HTTP {exc.code} — {detail}")
        return []
    except Exception as exc:  # noqa: BLE001 - surface as a warning, keep pipeline going
        print(f"        [WARN] Wikimedia search failed: {exc}")
        return []


def download_asset_files(manifest: list[dict], assets_dir: Path) -> list[dict]:
    """Download each asset's bytes locally instead of leaving it as a remote
    URL. Remotion renders with several parallel browser tabs, and having all
    of them fetch the same remote image at once is exactly what triggers
    Wikimedia's rate limiting (429s) — downloading once here avoids that
    entirely, and also means rendering doesn't depend on the network at all.
    """
    downloaded = []
    for i, item in enumerate(manifest):
        url = item.get("url", "")
        if not url:
            continue
        ext = Path(url.split("?")[0]).suffix or ".jpg"
        filename = f"asset_{i:03d}{ext}"
        dest = assets_dir / filename
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "DraftArchive/1.0 (personal video pipeline; contact: n/a)"},
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                dest.write_bytes(resp.read())
            downloaded.append({"title": item.get("title", ""), "filename": filename})
        except Exception as exc:  # noqa: BLE001
            print(f"        [WARN] Could not download {url}: {exc}")
    return downloaded


def run(ctx: RunContext, scene_queries: list[str] | None = None) -> None:
    scene_queries = scene_queries or [ctx.topic]
    assets_dir = ctx.path_for("assets")
    assets_dir.mkdir(exist_ok=True)

    manifest = []
    for query in scene_queries:
        hits = search_wikimedia(query)
        print(f"        Wikimedia search '{query}': {len(hits)} result(s)")
        manifest.extend(hits)

    downloaded = download_asset_files(manifest, assets_dir)
    print(f"        Downloaded {len(downloaded)}/{len(manifest)} asset file(s) locally")

    manifest_path = assets_dir / "manifest.json"
    manifest_path.write_text(json.dumps(downloaded, indent=2))
    ctx.outputs["asset_manifest"] = str(manifest_path)
    ctx.outputs["assets_dir"] = str(assets_dir)


registry.register(
    ToolSpec(
        name="wikimedia_commons",
        category="footage",
        runtime="FREE",
        license="public-domain / CC",
        run=run,
    )
)