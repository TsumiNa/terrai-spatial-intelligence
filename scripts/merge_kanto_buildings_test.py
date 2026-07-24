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
    # With no PLATEAU heights and no tags, both fall to a class estimate.
    assert by_source["osm"]["height_source"] == "estimate"
    assert by_source["osm"]["height"] == 6.0  # house
    assert by_source["fgd"]["height_source"] == "estimate"
    assert by_source["fgd"]["height"] == 9.0  # generic
    assert stats["height_source_split"] == {"plateau": 0, "osm_tag": 0, "estimate": 2}


def test_merge_bakes_three_tier_height(tmp_path: Path) -> None:
    osm = tmp_path / "osm.geojson"
    fgd = tmp_path / "fgd.geojson"
    plateau = tmp_path / "heights.geojson"
    write_collection(
        osm,
        [
            # A: a PLATEAU point falls inside -> measured height wins.
            {"type": "Feature", "geometry": square(139.600, 35.440), "properties": {"osm_id": 1, "building": "yes"}},
            # B: building:levels present, no PLATEAU -> osm_tag (5 * 3 m).
            {"type": "Feature", "geometry": square(139.610, 35.450), "properties": {"osm_id": 2, "building": "apartments", "building:levels": "5"}},
            # C: nothing -> class estimate (house = 6 m).
            {"type": "Feature", "geometry": square(139.615, 35.455), "properties": {"osm_id": 3, "building": "house"}},
        ],
    )
    write_collection(fgd, [])
    write_collection(
        plateau,
        [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [139.6005, 35.4405]}, "properties": {"height": 30.0}}],
    )

    stats = merge(osm, fgd, {MESH}, tmp_path / "out", plateau_path=plateau)

    assert stats["height_source_split"] == {"plateau": 1, "osm_tag": 1, "estimate": 1}
    lines = [json.loads(line) for line in (tmp_path / "out/merged.geojsonl").read_text().splitlines()]
    by_id = {f["properties"]["feature_id"]: f["properties"] for f in lines}
    assert by_id["osm:1"]["height"] == 30.0 and by_id["osm:1"]["height_source"] == "plateau"
    assert by_id["osm:2"]["height"] == 15.0 and by_id["osm:2"]["height_source"] == "osm_tag"
    assert by_id["osm:3"]["height"] == 6.0 and by_id["osm:3"]["height_source"] == "estimate"
