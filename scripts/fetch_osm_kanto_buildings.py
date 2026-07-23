"""Acquire mainland-Kanto OSM building footprints from a pinned extract.

The high-zoom detail layer needs buildings as data objects — stable ids,
tags, licence — which the rendering tiles cannot provide
(docs/refactor/osm-highzoom-detail/00-overview.md). This script walks a
pinned Geofabrik snapshot with pyosmium, keeps every closed way and
multipolygon tagged ``building=*`` whose bounding box intersects the
mainland-Kanto acquisition window, and streams the result into the
gitignored data tree with per-feature provenance.

Admission principle (docs/architecture/FL_SL_AL_CONCEPT.md): OSM qualifies as
FL — real GIS data, stable ids, ODbL with attribution.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterator

import osmium
import osmium.geom

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.fetch_mlit_foundation import StreamedCollection  # noqa: E402
from terrai_spatial.pipeline.http import download_file  # noqa: E402
from terrai_spatial.pipeline.io import write_json_atomic  # noqa: E402
from terrai_spatial.pipeline.provenance import utc_timestamp  # noqa: E402
from terrai_spatial.pipeline.regions import MLIT_ACQUISITION_BOUNDS  # noqa: E402
from terrai_spatial.store import feature_bbox  # noqa: E402

# A dated snapshot, never "-latest": the extract date is the vintage the data
# card and every feature cite, and a re-run reproduces the same inventory.
PBF_URL = "https://download.geofabrik.de/asia/japan/kanto-260101.osm.pbf"
DATASET_ID = "osm-kanto-buildings-260101"
OUTPUT = ROOT / "data/osm/kanto_buildings"
LICENSE = "Open Database License (ODbL) 1.0"
SCOPE = "TerrAI Kanto acquisition: OSM building footprints inside the mainland window"
WINDOW = MLIT_ACQUISITION_BOUNDS["kanto"]

# Tags kept on each feature; everything else the extract carries is dropped.
KEPT_TAGS = ("building", "name", "building:levels")


def _intersects_window(bbox: tuple[float, float, float, float]) -> bool:
    west, south, east, north = WINDOW
    return bbox[2] >= west and bbox[0] <= east and bbox[3] >= south and bbox[1] <= north


def _extract_timestamp(path: Path) -> str:
    reader = osmium.io.Reader(str(path), osmium.osm.NOTHING)
    try:
        stamp = reader.header().get("osmosis_replication_timestamp")
    finally:
        reader.close()
    return stamp or "2026-01-01 (extract date from the pinned snapshot name)"


def iter_building_features(
    path: Path, retrieved_at: str, source_updated_at: str, *, skipped: list[int] | None = None
) -> Iterator[dict[str, Any]]:
    """Every building area in the file that touches the Kanto window.

    OSM carries a small number of degenerate multipolygons; the geometry
    factory rejects them and they are skipped, counted into ``skipped`` so the
    manifest states the loss instead of hiding it.
    """

    factory = osmium.geom.GeoJSONFactory()
    processor = osmium.FileProcessor(str(path)).with_areas(osmium.filter.KeyFilter("building"))
    for candidate in processor:
        if not candidate.is_area() or "building" not in candidate.tags:
            continue
        try:
            geometry = json.loads(factory.create_multipolygon(candidate))
        except RuntimeError:
            if skipped is not None:
                skipped.append(candidate.orig_id())
            continue
        bbox = feature_bbox(geometry)
        if bbox is None or not _intersects_window(bbox):
            continue
        properties: dict[str, Any] = {
            "osm_id": candidate.orig_id(),
            "osm_type": "way" if candidate.from_way() else "relation",
        }
        for tag in KEPT_TAGS:
            if tag in candidate.tags:
                properties[tag] = candidate.tags[tag]
        properties.update(
            {
                "terrai_dataset_id": DATASET_ID,
                "terrai_region": "kanto",
                "terrai_source_archive": Path(PBF_URL).name,
                "terrai_source_updated_at": source_updated_at,
                "terrai_retrieved_at": retrieved_at,
                "terrai_source_url": PBF_URL,
            }
        )
        yield {"type": "Feature", "geometry": geometry, "properties": properties}


def build(*, output: Path = OUTPUT, source_path: Path | None = None) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    retrieved_at = utc_timestamp()
    with tempfile.TemporaryDirectory(prefix="terrai-osm-kanto-") as temporary:
        if source_path is None:
            source_path = Path(temporary) / Path(PBF_URL).name
            result = download_file(PBF_URL, source_path, timeout=1800)
            sha256 = result["sha256"]
        else:
            from terrai_spatial.pipeline.io import file_sha256

            sha256 = file_sha256(source_path)
        source_updated_at = _extract_timestamp(source_path)
        collection = StreamedCollection(
            output / "buildings.geojson",
            DATASET_ID,
            {
                "source_updated_at": source_updated_at,
                "retrieved_at": retrieved_at,
                "license": LICENSE,
                "scope": SCOPE,
            },
        )
        skipped: list[int] = []
        try:
            for feature in iter_building_features(source_path, retrieved_at, source_updated_at, skipped=skipped):
                collection.add(feature)
        except BaseException:
            collection.discard()
            raise
        collection.close()
    product = output / "buildings.geojson"
    try:
        product_path = str(product.relative_to(ROOT))
    except ValueError:  # test/offline runs write outside the repository
        product_path = str(product)
    manifest = {
        "retrieved_at": retrieved_at,
        "scope": SCOPE,
        "dataset_id": DATASET_ID,
        "output": product_path,
        "source_updated_at": source_updated_at,
        "license": LICENSE,
        "feature_count": collection.count,
        "invalid_geometries_skipped": len(skipped),
        "downloads": [{"url": PBF_URL, "sha256": sha256}],
    }
    write_json_atomic(output / "metadata.json", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="accepted for data-task compatibility")
    parser.parse_args()
    manifest = build()
    print(f"Wrote OSM Kanto buildings: {manifest['feature_count']} features")


if __name__ == "__main__":
    main()
