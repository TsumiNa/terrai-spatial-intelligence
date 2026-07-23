"""Derive the committed CI fixtures from the full Kanto acquisitions.

CI needs the shape of the foundation data, not its volume: the suites query a
handful of known windows. This script clips each acquired product — the ten
MLIT datasets and the OSM building footprints — to exactly those windows and
writes the committed fixture trees CI copies into place before building the
store (`data/mlit_fixture` → `data/mlit`, `data/osm_kanto_fixture` →
`data/osm/kanto_buildings`). Local and exhibition environments run the real
acquisitions instead; the products have one scope, and these fixtures are
test infrastructure derived from them.

Regenerate after an acquisition table or the windows below change:

    uv run python -m terrai_spatial data ensure --only ci_fixture --force
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.fetch_mlit_foundation import DATASETS, StreamedCollection  # noqa: E402
from terrai_spatial.pipeline.io import read_json_object, write_json_atomic  # noqa: E402
from terrai_spatial.pipeline.regions import Bounds  # noqa: E402
from terrai_spatial.store import feature_bbox, stream_feature_collection  # noqa: E402

SOURCE = ROOT / "data/mlit"
OUTPUT = ROOT / "data/mlit_fixture"
OSM_SOURCE = ROOT / "data/osm/kanto_buildings"
OSM_OUTPUT = ROOT / "data/osm_kanto_fixture"

# The union of every window a test suite queries, with margin:
# - "yokohama" covers the Playwright foundation suite's zoom-16 viewport and
#   its keyboard pans, plus the identity matrix's Yokohama window;
# - the other three are the identity matrix's coverage windows, padded.
FIXTURE_WINDOWS: dict[str, Bounds] = {
    "yokohama": (139.56, 35.42, 139.62, 35.48),
    "tokyo": (139.68, 35.67, 139.72, 35.71),
    "koshigaya": (139.75, 35.85, 139.81, 35.91),
    "hachioji": (139.25, 35.61, 139.31, 35.67),
}


# The OSM building product is an order of magnitude denser than any MLIT
# layer; clipping it through the shared windows produced a 97 MB fixture.
# Its fixture keeps only the two windows the suites actually query, tightly:
# the Playwright handover viewport (with pan margin) and the identity
# matrix's Tokyo window.
OSM_FIXTURE_WINDOWS: dict[str, Bounds] = {
    "yokohama": (139.578, 35.438, 139.602, 35.455),
    "tokyo": (139.69, 35.68, 139.71, 35.70),
}


def _intersects_any(bbox: tuple[float, float, float, float], windows: dict[str, Bounds] = FIXTURE_WINDOWS) -> bool:
    min_x, min_y, max_x, max_y = bbox
    return any(
        max_x >= west and min_x <= east and max_y >= south and min_y <= north
        for west, south, east, north in windows.values()
    )


def build(*, source: Path = SOURCE, output: Path = OUTPUT) -> dict[str, Any]:
    source_manifest = read_json_object(source / "metadata.json", label="mlit manifest")
    output.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {
        "purpose": "CI test fixture: the exact windows the suites query, derived from a full acquisition",
        "derived_from": {
            "retrieved_at": source_manifest.get("retrieved_at"),
            "scope": source_manifest.get("scope"),
        },
        "windows": {name: list(bounds) for name, bounds in FIXTURE_WINDOWS.items()},
        "datasets": {},
    }
    for dataset in DATASETS:
        envelope, features = stream_feature_collection(source / dataset.output)
        collection: StreamedCollection | None = None
        try:
            for feature in features:
                bbox = feature_bbox(feature.get("geometry"))
                if bbox is None or not _intersects_any(bbox):
                    continue
                if collection is None:
                    metadata = dict(envelope.get("metadata") or {})
                    metadata["scope"] = f"CI fixture windows derived from: {metadata.get('scope', 'unknown scope')}"
                    collection = StreamedCollection(output / dataset.output, dataset.dataset_id, metadata)
                collection.add(feature)
        except BaseException:
            if collection is not None:
                collection.discard()
            raise
        finally:
            # An exception above would otherwise leave the source handle to GC.
            features.close()
        if collection is None:
            metadata = dict(envelope.get("metadata") or {})
            metadata["scope"] = f"CI fixture windows derived from: {metadata.get('scope', 'unknown scope')}"
            collection = StreamedCollection(output / dataset.output, dataset.dataset_id, metadata)
        collection.close()
        manifest["datasets"][dataset.key] = {
            "output": f"data/mlit_fixture/{dataset.output}",
            "feature_count": collection.count,
            "source_updated_at": dataset.source_updated_at,
            "license": dataset.license,
            "retrieved_at": source_manifest.get("retrieved_at"),
        }
        print(f"[mlit-fixture] {dataset.key}: {collection.count} features", flush=True)
    write_json_atomic(output / "metadata.json", manifest)
    return manifest


def build_osm_buildings(*, source: Path = OSM_SOURCE, output: Path = OSM_OUTPUT) -> dict[str, Any]:
    """Clip the OSM building product through the same suite windows."""

    source_manifest = read_json_object(source / "metadata.json", label="osm kanto manifest")
    output.mkdir(parents=True, exist_ok=True)
    envelope, features = stream_feature_collection(source / "buildings.geojson")
    collection: StreamedCollection | None = None
    try:
        for feature in features:
            bbox = feature_bbox(feature.get("geometry"))
            if bbox is None or not _intersects_any(bbox, OSM_FIXTURE_WINDOWS):
                continue
            if collection is None:
                metadata = dict(envelope.get("metadata") or {})
                metadata["scope"] = f"CI fixture windows derived from: {metadata.get('scope', 'unknown scope')}"
                collection = StreamedCollection(output / "buildings.geojson", str(envelope.get("name", "osm-kanto-buildings")), metadata)
            collection.add(feature)
    except BaseException:
        if collection is not None:
            collection.discard()
        features.close()
        raise
    finally:
        features.close()
    if collection is None:
        metadata = dict(envelope.get("metadata") or {})
        metadata["scope"] = f"CI fixture windows derived from: {metadata.get('scope', 'unknown scope')}"
        collection = StreamedCollection(output / "buildings.geojson", str(envelope.get("name", "osm-kanto-buildings")), metadata)
    collection.close()
    manifest = {
        "purpose": "CI test fixture: the exact windows the suites query, derived from a full acquisition",
        "derived_from": {
            "retrieved_at": source_manifest.get("retrieved_at"),
            "scope": source_manifest.get("scope"),
        },
        "windows": {name: list(bounds) for name, bounds in OSM_FIXTURE_WINDOWS.items()},
        "dataset_id": source_manifest.get("dataset_id"),
        "source_updated_at": source_manifest.get("source_updated_at"),
        "license": source_manifest.get("license"),
        "feature_count": collection.count,
        "output": "data/osm_kanto_fixture/buildings.geojson",
    }
    write_json_atomic(output / "metadata.json", manifest)
    print(f"[ci-fixture] osmBuildings: {collection.count} features", flush=True)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="accepted for data-task compatibility")
    parser.parse_args()
    manifest = build()
    counts = ", ".join(f"{key}={row['feature_count']}" for key, row in manifest["datasets"].items())
    osm_manifest = build_osm_buildings()
    print(f"Wrote CI fixtures: {counts}, osmBuildings={osm_manifest['feature_count']}")


if __name__ == "__main__":
    main()
