#!/usr/bin/env python3
"""Cache GSI visual tiles used by the two TerrAI demo regions.

Sources:
  std           - GSI standard map
  seamlessphoto - nationwide latest orthophoto / satellite mosaic
  hillshademap  - DEM-derived hillshade
  slopemap      - DEM-derived slope map

The downloaded files are small, area-limited snapshots for a reproducible PoC.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import math
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from terrai_spatial.pipeline.http import download_bytes  # noqa: E402
from terrai_spatial.pipeline.io import write_json_atomic  # noqa: E402
from terrai_spatial.pipeline.regions import STUDY_BOUNDS  # noqa: E402

BASE = "https://cyberjapandata.gsi.go.jp/xyz"
# Imagery stays `seamlessphoto` and the cache reaches its real z18 ceiling —
# decision landed in docs/refactor/maplibre-migration/03-maplibre-basemap-pr3.md:
# in both demo regions `ort` serves the same ortho mosaic at roughly triple the
# bytes per z18 tile (58.8 KB vs 17.7 KB, sampled 2026-07-21).
LAYERS = {
    "standard": ("std", "png", range(15, 16)),
    "photo": ("seamlessphoto", "jpg", range(15, 19)),
    "hillshade": ("hillshademap", "png", range(15, 17)),
    "slope": ("slopemap", "png", range(15, 16)),
}


def target_path(job: tuple[str, str, str, int, int, int, bool]) -> Path:
    region, local_layer, remote_layer, zoom, x, y, force = job
    extension = LAYERS[local_layer][1]
    layer_path = Path() if local_layer == "standard" else Path(local_layer)
    return ROOT / "data" / "tiles" / region / layer_path / str(zoom) / f"{x}-{y}.{extension}"


def fetch(job: tuple[str, str, str, int, int, int, bool]) -> tuple[str, bool, str]:
    region, local_layer, remote_layer, zoom, x, y, force = job
    extension = LAYERS[local_layer][1]
    target = target_path(job)
    if not force and target.exists() and target.stat().st_size > 200:
        return str(target.relative_to(ROOT)), True, "cached"
    target.parent.mkdir(parents=True, exist_ok=True)
    url = f"{BASE}/{remote_layer}/{zoom}/{x}/{y}.{extension}"
    try:
        payload = download_bytes(url, timeout=30)
        if len(payload) < 200:
            raise ValueError("empty or placeholder tile")
        target.write_bytes(payload)
        return str(target.relative_to(ROOT)), True, "downloaded"
    except (RuntimeError, ValueError) as error:
        return str(target.relative_to(ROOT)), False, str(error)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="refresh tiles even when a cache file exists")
    parser.add_argument("--manifest-only", action="store_true", help="write the manifest from an already complete cache")
    args = parser.parse_args()
    jobs = []
    for region, (west, south, east, north) in STUDY_BOUNDS.items():
        for local_layer, (remote_layer, _, zooms) in LAYERS.items():
            for zoom in zooms:
                scale = 2**zoom
                west_x = int((west + 180) / 360 * scale)
                east_x = int((east + 180) / 360 * scale)
                north_y = int((1 - math.asinh(math.tan(math.radians(north))) / math.pi) / 2 * scale)
                south_y = int((1 - math.asinh(math.tan(math.radians(south))) / math.pi) / 2 * scale)
                for x in range(west_x, east_x + 1):
                    for y in range(north_y, south_y + 1):
                        jobs.append((region, local_layer, remote_layer, zoom, x, y, args.force))

    failures = []
    if args.manifest_only:
        for job in jobs:
            path = target_path(job)
            if not path.is_file() or path.stat().st_size <= 200:
                failures.append((str(path.relative_to(ROOT)), "missing or empty"))
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            for path, ok, status in executor.map(fetch, jobs):
                if not ok:
                    failures.append((path, status))
    downloaded = len(jobs) - len(failures)
    print(f"Visual tiles ready: {downloaded}/{len(jobs)}")
    for path, error in failures:
        print(f"FAILED {path}: {error}")
    if failures:
        raise SystemExit(1)
    manifest = {
        "source": "GSI XYZ tiles",
        "layers": {name: remote for name, (remote, _, _) in LAYERS.items()},
        "files": sorted(str(target_path(job).relative_to(ROOT)) for job in jobs),
    }
    write_json_atomic(ROOT / "data" / "tiles" / "manifest.json", manifest)
    time.sleep(0.1)


if __name__ == "__main__":
    main()
