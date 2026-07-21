#!/usr/bin/env python3
"""Restore missing packaged data snapshots from the TerrAI GitHub repository."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from terrai_spatial.pipeline.http import download_bytes  # noqa: E402
from terrai_spatial.pipeline.io import valid_data_file, write_bytes_atomic  # noqa: E402

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
        headers = {}
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        payload = download_bytes(f"{BASE_URL}/{quoted}", timeout=45, headers=headers)
        source = BASE_URL
    if not payload:
        raise RuntimeError(f"empty bootstrap response for {relative}")
    write_bytes_atomic(target, payload)
    print(f"Restored {relative} from {source}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="replace existing packaged snapshots")
    parser.add_argument("--offline", action="store_true", help="restore only from the local Git object database")
    args = parser.parse_args()
    restored = 0
    for relative in FILES:
        target = ROOT / relative
        if not args.force and valid_data_file(target):
            continue
        download(relative, args.offline)
        restored += 1
    print(f"Packaged data ready: {len(FILES) - restored} cached, {restored} restored")


if __name__ == "__main__":
    main()
