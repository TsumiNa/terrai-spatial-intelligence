"""Derive the committed CI fixture from a full MLIT Kanto acquisition.

CI needs the shape of the foundation data, not its volume: the suites query a
handful of known windows, and fetching 2.3 GB from MLIT on every cache miss
made CI unacceptably slow. This script clips each acquired product to exactly
those windows and writes `data/mlit_fixture/` — a small committed artifact CI
copies into `data/mlit` before building the store. Local and exhibition
environments run the real acquisition (`fetch mlit`) instead; the product has
one scope, and this fixture is test infrastructure derived from it.

Regenerate after the acquisition table or the windows below change:

    uv run python -m terrai_spatial data ensure --only mlit_fixture --force
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


def _intersects_any(bbox: tuple[float, float, float, float]) -> bool:
    min_x, min_y, max_x, max_y = bbox
    return any(
        max_x >= west and min_x <= east and max_y >= south and min_y <= north
        for west, south, east, north in FIXTURE_WINDOWS.values()
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="accepted for data-task compatibility")
    parser.parse_args()
    manifest = build()
    counts = ", ".join(f"{key}={row['feature_count']}" for key, row in manifest["datasets"].items())
    print(f"Wrote MLIT CI fixture: {counts}")


if __name__ == "__main__":
    main()
