#!/usr/bin/env python3
"""Restore missing packaged data snapshots from the TerrAI GitHub repository."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get(
    "TERRAI_BOOTSTRAP_BASE_URL",
    "https://raw.githubusercontent.com/TsumiNa/terrai-spatial-intelligence/main",
).rstrip("/")

FILES = (
    "data/external/source_registry.json",
    "data/external/yokohama/hinanjo_20260401.csv",
    "data/yokohama/building_risk.geojson",
    "data/yokohama/building_summary.json",
    "data/yokohama/road_priority.geojson",
    "data/yokohama/road_summary.json",
    "data/mobara/context.geojson",
    "data/mobara/site_cells.geojson",
    "data/mobara/solar_summary.json",
    "data/mobara/tepco_grid_screen.json",
)


def from_git(relative: str) -> bytes | None:
    try:
        result = subprocess.run(
            ["git", "show", f"HEAD:{relative}"],
            cwd=ROOT,
            check=False,
            capture_output=True,
        )
    except FileNotFoundError:
        return None
    return result.stdout if result.returncode == 0 and result.stdout else None


def download(relative: str, offline: bool) -> None:
    target = ROOT / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = from_git(relative)
    source = "Git HEAD"
    if payload is None:
        if offline:
            raise RuntimeError(f"{relative} is unavailable in Git HEAD and network access is disabled")
        quoted = urllib.parse.quote(relative, safe="/")
        headers = {"User-Agent": "TerrAI-data-bootstrap/1.0"}
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        request = urllib.request.Request(f"{BASE_URL}/{quoted}", headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                payload = response.read()
        except (urllib.error.URLError, TimeoutError) as error:
            raise RuntimeError(f"failed to restore {relative} from {BASE_URL}: {error}") from error
        source = BASE_URL
    if not payload:
        raise RuntimeError(f"empty bootstrap response for {relative}")
    with tempfile.NamedTemporaryFile(dir=target.parent, prefix=f".{target.name}.", delete=False) as handle:
        handle.write(payload)
        temporary = Path(handle.name)
    temporary.replace(target)
    print(f"Restored {relative} from {source}")


def ready(path: Path) -> bool:
    if not path.is_file() or path.stat().st_size == 0:
        return False
    if path.suffix not in {".json", ".geojson"}:
        return True
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return path.suffix != ".geojson" or value.get("type") == "FeatureCollection"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="replace existing packaged snapshots")
    parser.add_argument("--offline", action="store_true", help="restore only from the local Git object database")
    args = parser.parse_args()
    restored = 0
    for relative in FILES:
        target = ROOT / relative
        if not args.force and ready(target):
            continue
        download(relative, args.offline)
        restored += 1
    print(f"Packaged data ready: {len(FILES) - restored} cached, {restored} restored")


if __name__ == "__main__":
    main()
