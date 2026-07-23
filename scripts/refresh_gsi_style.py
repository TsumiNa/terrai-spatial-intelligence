#!/usr/bin/env python3
"""Refresh the pinned GSI vector style + sprite snapshot the webapp serves.

The map loads a repo-owned copy of the GSI experimental vector style and sprite
(basemap-resilience) instead of fetching the experimental GitHub Pages host at
runtime, so that host dying can never stop the map from constructing. Upstream
occasionally updates the style; this makes the refresh a deliberate, reviewable
act: fetch upstream, print a diff summary, and (with --write) overwrite the
vendored files and stamp the provenance.

    uv run python scripts/refresh_gsi_style.py           # dry-run diff summary
    uv run python scripts/refresh_gsi_style.py --write    # overwrite + restamp
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from terrai_spatial.pipeline.http import download_bytes  # noqa: E402
from terrai_spatial.pipeline.io import write_bytes_atomic, write_text_atomic  # noqa: E402
from terrai_spatial.pipeline.provenance import utc_timestamp  # noqa: E402

STYLE_URL = "https://gsi-cyberjapan.github.io/gsivectortile-mapbox-gl-js/std.json"
SPRITE_BASE = "https://gsi-cyberjapan.github.io/gsivectortile-mapbox-gl-js/sprite"
SPRITE_FILES = ("std.json", "std.png", "std@2x.json", "std@2x.png")

BASEMAP_DIR = ROOT / "webapp" / "public" / "basemap"
STYLE_PATH = BASEMAP_DIR / "gsi-std-style.json"
PROVENANCE_PATH = BASEMAP_DIR / "gsi-std-style.provenance.json"
SPRITE_DIR = BASEMAP_DIR / "sprite"


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _layer_count(payload: bytes) -> int:
    try:
        return len(json.loads(payload).get("layers", []))
    except (ValueError, AttributeError):
        return -1


def _summarize(name: str, current: bytes | None, upstream: bytes) -> bool:
    """Print a one-line diff summary; return True if the file changed."""
    changed = current != upstream
    mark = "CHANGED" if changed else "same"
    detail = ""
    if name == "gsi-std-style.json":
        detail = f" (layers {_layer_count(current or b'')} -> {_layer_count(upstream)})"
    print(
        f"  [{mark:7}] {name}: {len(upstream)} bytes, sha {_sha256(upstream)[:12]}{detail}"
    )
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Refresh the pinned GSI style + sprite snapshot."
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="overwrite the vendored files and restamp provenance",
    )
    args = parser.parse_args()

    fetched: dict[Path, bytes] = {}
    any_changed = False

    print("Style:")
    upstream_style = download_bytes(STYLE_URL)
    fetched[STYLE_PATH] = upstream_style
    current_style = STYLE_PATH.read_bytes() if STYLE_PATH.is_file() else None
    any_changed |= _summarize("gsi-std-style.json", current_style, upstream_style)

    print("Sprite:")
    for name in SPRITE_FILES:
        upstream = download_bytes(f"{SPRITE_BASE}/{name}")
        path = SPRITE_DIR / name
        fetched[path] = upstream
        current = path.read_bytes() if path.is_file() else None
        any_changed |= _summarize(name, current, upstream)

    if not args.write:
        print(
            "\nDry run."
            + (
                " Upstream differs — rerun with --write to update."
                if any_changed
                else " No changes."
            )
        )
        return 0

    for path, payload in fetched.items():
        write_bytes_atomic(path, payload)
    provenance = {
        "source_style": STYLE_URL,
        "source_sprite": f"{SPRITE_BASE}/std",
        "retrieved": utc_timestamp(),
        "style_sha256": _sha256(upstream_style),
        "sprite_png_sha256": _sha256(fetched[SPRITE_DIR / "std.png"]),
        "note": (
            "Pinned snapshot of the GSI experimental vector style + sprite. Style is "
            "byte-identical to upstream; the sprite URL is repointed to the local "
            "/basemap/sprite/std at compose time. glyphs (maps.gsi.go.jp) and tiles "
            "(cyberjapandata) stay live."
        ),
    }
    write_text_atomic(
        PROVENANCE_PATH, json.dumps(provenance, indent=2, ensure_ascii=False) + "\n"
    )
    print("\nWrote vendored snapshot and restamped provenance.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
