#!/usr/bin/env python3
"""Cache GSI visual tiles used by the two TerrAI demo regions.

Sources:
  seamlessphoto - nationwide latest orthophoto / satellite mosaic
  hillshademap  - DEM-derived hillshade
  slopemap      - DEM-derived slope map

The downloaded files are small, area-limited snapshots for a reproducible PoC.
"""

from __future__ import annotations

import concurrent.futures
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
    "photo": ("seamlessphoto", "jpg", range(15, 18)),
    "hillshade": ("hillshademap", "png", range(15, 17)),
    "slope": ("slopemap", "png", range(15, 16)),
}


def fetch(job: tuple[str, str, str, int, int, int]) -> tuple[str, bool, str]:
    region, local_layer, remote_layer, zoom, x, y = job
    extension = LAYERS[local_layer][1]
    target = ROOT / "data" / "tiles" / region / local_layer / str(zoom) / f"{x}-{y}.{extension}"
    if target.exists() and target.stat().st_size > 200:
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
                        jobs.append((region, local_layer, remote_layer, zoom, x, y))

    failures = []
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
    time.sleep(0.1)


if __name__ == "__main__":
    main()
