"""Merge OSM (primary) + 基盤地図情報 (fill) Kanto buildings into one tile source.

The self-built basemap (docs/refactor/osm-basemap-tiles/00-overview.md) needs a
single building inventory with no double-drawing: OSM where it exists (stable ids,
primary), government footprints filling OSM's suburban and rural gaps, one
consistent coverage. This is that build-time merge — affordable once, offline —
producing a line-delimited GeoJSON the tile step (tippecanoe) turns into PMTiles.

Three rules, from the overview:

1. **Coverage clip.** Both layers are clipped to the FGD coverage footprint
   (``data/fgd/kanto_buildings/coverage.json`` — the 180 mainland 2次メッシュ). OSM
   reaches slightly past it (into Ibaraki, eastern Chiba); those footprints are
   dropped so the merged coverage is exactly the government footprint (the owner's
   "align OSM to the FGD range").
2. **OSM primary.** Every in-coverage OSM building is kept, its identity winning.
3. **FGD fills the gaps.** A government footprint is kept only where **no** OSM
   building covers that ground — tested by whether the FGD footprint's
   representative point falls inside any OSM footprint (an STRtree lookup). Where
   OSM already has the building, its identity wins and the FGD copy is dropped, so
   the layer never double-draws.

Every output feature carries **only the baked render/identity schema** —
``feature_id`` (``osm:<id>`` / ``fgd:<id>``), ``footprint_source`` (``osm`` |
``fgd``) and ``building`` class — not OSM's full tag set: the tiles carry
render/identity, analytical attributes stay in the source (the overview's
render/analyse boundary). Height/height_source are added by PR4 (PLATEAU).

The representative-point test is fast and correct for the common case (OSM and
FGD footprints of the same building overlap at the centre). Offset digitisation
in dense blocks can leak a few doubles or gaps; an area-overlap threshold is the
documented refinement (see the PR plan). Coordinates: OSM is WGS84, FGD is JGD2024
— identical to sub-metre in Japan, so no reprojection.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import fiona
from shapely.geometry import mapping, shape
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from terrai_spatial.pipeline.io import write_json_atomic  # noqa: E402
from terrai_spatial.pipeline.provenance import utc_timestamp  # noqa: E402

OSM_GEOJSON = ROOT / "data/osm/kanto_buildings/buildings.geojson"
FGD_GEOJSON = ROOT / "data/fgd/kanto_buildings/buildings.geojson"
COVERAGE_JSON = ROOT / "data/fgd/kanto_buildings/coverage.json"
OUTPUT = ROOT / "data/tiles/kanto_buildings"
MERGED_NAME = "merged.geojsonl"
PMTILES_NAME = "buildings.pmtiles"
TILE_LAYER = "buildings"
MIN_ZOOM = 0
MAX_ZOOM = 16

# 2次メッシュ cell size (must match scripts/fetch_fgd_kanto_buildings.py).
MESH_LAT_DEG = 1 / 12
MESH_LON_DEG = 1 / 8


def lonlat_to_mesh(lon: float, lat: float) -> str:
    """The 6-digit 2次メッシュ code a point falls in (inverse of ``mesh_cell``)."""

    ab = int(lat * 1.5)
    cd = int(lon - 100)
    row = min(7, max(0, int((lat - ab / 1.5) / MESH_LAT_DEG)))
    col = min(7, max(0, int((lon - (cd + 100)) / MESH_LON_DEG)))
    return f"{ab:02d}{cd:02d}{row}{col}"


def load_coverage_meshes(coverage_path: Path) -> set[str]:
    return set(json.loads(coverage_path.read_text(encoding="utf-8"))["meshes"])


def _write_feature(handle: Any, geometry: Any, properties: dict[str, Any]) -> None:
    record = {"type": "Feature", "geometry": mapping(geometry), "properties": properties}
    handle.write(json.dumps(record, ensure_ascii=False))
    handle.write("\n")


def merge(
    osm_path: Path,
    fgd_path: Path,
    coverage_meshes: set[str],
    output_dir: Path,
) -> dict[str, Any]:
    """Write the merged line-delimited GeoJSON and return the merge statistics."""

    output_dir.mkdir(parents=True, exist_ok=True)
    merged_path = output_dir / MERGED_NAME
    osm_kept = osm_clipped = 0
    osm_geoms: list[Any] = []

    with merged_path.open("w", encoding="utf-8") as handle:
        with fiona.open(osm_path) as osm:
            for feature in osm:
                geometry = shape(feature.geometry)
                point = geometry.representative_point()
                if lonlat_to_mesh(point.x, point.y) not in coverage_meshes:
                    osm_clipped += 1
                    continue
                properties = dict(feature.properties)
                _write_feature(
                    handle,
                    geometry,
                    {
                        "feature_id": f"osm:{properties.get('osm_id')}",
                        "footprint_source": "osm",
                        "building": properties.get("building", "yes"),
                    },
                )
                osm_geoms.append(geometry)
                osm_kept += 1

        # OSM is primary: an FGD footprint survives only where no OSM footprint
        # covers its representative point.
        tree = STRtree(osm_geoms)
        fgd_kept = fgd_dropped = 0
        with fiona.open(fgd_path) as fgd:
            for feature in fgd:
                geometry = shape(feature.geometry)
                point = geometry.representative_point()
                if tree.query(point, predicate="intersects").size:
                    fgd_dropped += 1
                    continue
                properties = dict(feature.properties)
                _write_feature(
                    handle,
                    geometry,
                    {
                        "feature_id": f"fgd:{properties.get('fgd_id')}",
                        "footprint_source": "fgd",
                        "building": "yes",
                    },
                )
                fgd_kept += 1

    return {
        "output": str(merged_path.relative_to(ROOT)) if merged_path.is_relative_to(ROOT) else str(merged_path),
        "feature_count": osm_kept + fgd_kept,
        "osm_kept": osm_kept,
        "osm_clipped_outside_coverage": osm_clipped,
        "fgd_kept": fgd_kept,
        "fgd_dropped_covered_by_osm": fgd_dropped,
    }


def generate_tiles(merged_path: Path, output_dir: Path) -> dict[str, Any]:
    """Run tippecanoe over the merged features to build the PMTiles."""

    pmtiles_path = output_dir / PMTILES_NAME
    command = [
        "tippecanoe",
        "-o",
        str(pmtiles_path),
        "-Z",
        str(MIN_ZOOM),
        "-z",
        str(MAX_ZOOM),
        "-l",
        TILE_LAYER,
        "--drop-densest-as-needed",
        "--extend-zooms-if-still-dropping",
        "--force",
        str(merged_path),
    ]
    subprocess.run(command, check=True)
    return {
        "output": str(pmtiles_path.relative_to(ROOT)) if pmtiles_path.is_relative_to(ROOT) else str(pmtiles_path),
        "size_bytes": pmtiles_path.stat().st_size,
        "min_zoom": MIN_ZOOM,
        "max_zoom": MAX_ZOOM,
        "layer": TILE_LAYER,
        "tool": "tippecanoe",
    }


def build(*, output: Path = OUTPUT, osm_path: Path = OSM_GEOJSON, fgd_path: Path = FGD_GEOJSON,
          coverage_path: Path = COVERAGE_JSON, tiles: bool = True) -> dict[str, Any]:
    coverage_meshes = load_coverage_meshes(coverage_path)
    retrieved_at = utc_timestamp()
    stats = merge(osm_path, fgd_path, coverage_meshes, output)
    manifest: dict[str, Any] = {
        "retrieved_at": retrieved_at,
        "scope": "TerrAI merged Kanto building tile source: OSM primary, 基盤地図情報 fill",
        "coverage_mesh_count": len(coverage_meshes),
        "merge": stats,
        "schema": ["feature_id", "footprint_source", "building"],
    }
    if tiles:
        manifest["tiles"] = generate_tiles(output / MERGED_NAME, output)
    write_json_atomic(output / "metadata.json", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="accepted for data-task compatibility")
    parser.add_argument("--no-tiles", action="store_true", help="write the merged GeoJSON without running tippecanoe")
    args = parser.parse_args()
    manifest = build(tiles=not args.no_tiles)
    merge_stats = manifest["merge"]
    print(
        f"Merged {merge_stats['feature_count']} buildings "
        f"(OSM {merge_stats['osm_kept']} kept / {merge_stats['osm_clipped_outside_coverage']} clipped; "
        f"FGD {merge_stats['fgd_kept']} fill / {merge_stats['fgd_dropped_covered_by_osm']} dropped)"
    )


if __name__ == "__main__":
    main()
