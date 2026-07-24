import json
from pathlib import Path

from scripts.merge_kanto_buildings import lonlat_to_mesh, merge

MESH = "533914"  # covered mainland mesh (lon 139.5–139.625, lat 35.417–35.5)


def square(x: float, y: float, size: float = 0.001) -> dict:
    return {
        "type": "Polygon",
        "coordinates": [[[x, y], [x + size, y], [x + size, y + size], [x, y + size], [x, y]]],
    }


def write_collection(path: Path, features: list[dict]) -> None:
    path.write_text(
        json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False),
        encoding="utf-8",
    )


def test_lonlat_to_mesh_round_trips_the_covered_cell() -> None:
    assert lonlat_to_mesh(139.60, 35.44) == MESH
    assert lonlat_to_mesh(140.99, 36.45) != MESH  # north-east, outside the coverage


def test_merge_clips_osm_keeps_primary_and_fills_with_fgd(tmp_path: Path) -> None:
    osm = tmp_path / "osm.geojson"
    fgd = tmp_path / "fgd.geojson"
    write_collection(
        osm,
        [
            # In-coverage OSM building — kept as primary.
            {"type": "Feature", "geometry": square(139.600, 35.440), "properties": {"osm_id": 100, "building": "house"}},
            # Outside the coverage mesh — clipped.
            {"type": "Feature", "geometry": square(140.990, 36.450), "properties": {"osm_id": 200, "building": "yes"}},
        ],
    )
    write_collection(
        fgd,
        [
            # Overlaps OSM 100 (its representative point falls inside it) — dropped.
            {"type": "Feature", "geometry": square(139.6003, 35.4403), "properties": {"fgd_id": "fgoid:X"}},
            # Empty ground in the covered mesh, no OSM — kept as fill.
            {"type": "Feature", "geometry": square(139.610, 35.450), "properties": {"fgd_id": "fgoid:Y"}},
        ],
    )

    stats = merge(osm, fgd, {MESH}, tmp_path / "out")

    assert stats["osm_kept"] == 1
    assert stats["osm_clipped_outside_coverage"] == 1
    assert stats["fgd_kept"] == 1
    assert stats["fgd_dropped_covered_by_osm"] == 1
    assert stats["feature_count"] == 2

    lines = [json.loads(line) for line in (tmp_path / "out/merged.geojsonl").read_text().splitlines()]
    by_source = {f["properties"]["footprint_source"]: f["properties"] for f in lines}
    assert by_source["osm"]["feature_id"] == "osm:100"
    assert by_source["osm"]["building"] == "house"
    assert by_source["fgd"]["feature_id"] == "fgd:fgoid:Y"
    assert by_source["fgd"]["building"] == "yes"
