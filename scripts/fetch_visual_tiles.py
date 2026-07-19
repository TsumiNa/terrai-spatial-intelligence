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
import json
import math
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = "https://cyberjapandata.gsi.go.jp/xyz"
REGIONS = {
    "yokohama": {"south": 35.4426, "west": 139.5835, "north": 35.4504, "east": 139.5935},
    "mobara": {"south": 35.4387, "west": 140.2757, "north": 35.4513, "east": 140.2913},
}
LAYERS = {
    "standard": ("std", "png", range(15, 16)),
    "photo": ("seamlessphoto", "jpg", range(15, 18)),
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
    request = urllib.request.Request(url, headers={"User-Agent": "TerrAI-open-data-PoC/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = response.read()
        if len(payload) < 200:
            raise ValueError("empty or placeholder tile")
        target.write_bytes(payload)
        return str(target.relative_to(ROOT)), True, "downloaded"
    except (urllib.error.URLError, TimeoutError, ValueError) as error:
        return str(target.relative_to(ROOT)), False, str(error)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="refresh tiles even when a cache file exists")
    parser.add_argument("--manifest-only", action="store_true", help="write the manifest from an already complete cache")
    args = parser.parse_args()
    jobs = []
    for region, bounds in REGIONS.items():
        for local_layer, (remote_layer, _, zooms) in LAYERS.items():
            for zoom in zooms:
                scale = 2**zoom
                west_x = int((bounds["west"] + 180) / 360 * scale)
                east_x = int((bounds["east"] + 180) / 360 * scale)
                north_y = int((1 - math.asinh(math.tan(math.radians(bounds["north"]))) / math.pi) / 2 * scale)
                south_y = int((1 - math.asinh(math.tan(math.radians(bounds["south"]))) / math.pi) / 2 * scale)
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
    manifest_path = ROOT / "data" / "tiles" / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    time.sleep(0.1)


if __name__ == "__main__":
    main()
