import json
from pathlib import Path

import osmium
from osmium.osm import mutable

from scripts.fetch_osm_kanto_buildings import (
    PBF_URL,
    WINDOW,
    _intersects_window,
    build,
    iter_building_features,
)


def write_fixture(path: Path) -> None:
    """A building inside the window, a non-building ring, and a building far
    outside — closed ways with real node locations."""

    writer = osmium.SimpleWriter(str(path))

    def node(node_id: int, lon: float, lat: float) -> None:
        writer.add_node(mutable.Node(id=node_id, location=(lon, lat), version=1))

    node(1, 139.6, 35.44)
    node(2, 139.601, 35.44)
    node(3, 139.601, 35.441)
    node(4, 139.6, 35.441)
    node(11, 0.0, 0.0)
    node(12, 0.001, 0.0)
    node(13, 0.001, 0.001)
    node(14, 0.0, 0.001)
    writer.add_way(
        mutable.Way(id=100, nodes=[1, 2, 3, 4, 1], version=1, tags={"building": "house", "name": "テスト", "building:levels": "2"})
    )
    writer.add_way(mutable.Way(id=200, nodes=[1, 2, 3, 1], version=1, tags={"highway": "residential"}))
    writer.add_way(mutable.Way(id=300, nodes=[11, 12, 13, 14, 11], version=1, tags={"building": "yes"}))
    writer.close()


def test_window_intersection_uses_the_kanto_bounds() -> None:
    west, south, east, north = WINDOW
    assert _intersects_window((west + 0.1, south + 0.1, west + 0.2, south + 0.2))
    assert _intersects_window((west - 0.1, south + 0.1, west + 0.1, south + 0.2))  # straddling
    assert not _intersects_window((0.0, 0.0, 1.0, 1.0))


def test_only_in_window_buildings_survive_with_identity_and_provenance(tmp_path: Path) -> None:
    fixture = tmp_path / "toy.osm"
    write_fixture(fixture)

    features = list(iter_building_features(fixture, "2026-07-23T00:00:00Z", "2026-01-01"))

    assert len(features) == 1
    feature = features[0]
    assert feature["geometry"]["type"] == "MultiPolygon"
    properties = feature["properties"]
    assert properties["osm_id"] == 100
    assert properties["osm_type"] == "way"
    assert properties["building"] == "house"
    assert properties["name"] == "テスト"
    assert properties["building:levels"] == "2"
    assert properties["terrai_source_url"] == PBF_URL
    assert properties["terrai_retrieved_at"] == "2026-07-23T00:00:00Z"
    assert properties["terrai_source_updated_at"] == "2026-01-01"


def test_build_writes_a_valid_collection_and_manifest_offline(tmp_path: Path) -> None:
    fixture = tmp_path / "toy.osm"
    write_fixture(fixture)

    manifest = build(output=tmp_path / "out", source_path=fixture)

    collection = json.loads((tmp_path / "out/buildings.geojson").read_text(encoding="utf-8"))
    assert collection["type"] == "FeatureCollection"
    assert collection["metadata"]["license"].startswith("Open Database License")
    assert len(collection["features"]) == 1
    assert manifest["feature_count"] == 1
    assert manifest["downloads"][0]["url"] == PBF_URL
    assert manifest["downloads"][0]["sha256"]
    written = json.loads((tmp_path / "out/metadata.json").read_text(encoding="utf-8"))
    assert written == manifest
