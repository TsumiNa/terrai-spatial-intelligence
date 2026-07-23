import json
from pathlib import Path

from scripts.build_ci_fixture import FIXTURE_WINDOWS, OSM_FIXTURE_WINDOWS, _intersects_any, build, build_osm_buildings
from scripts.fetch_mlit_foundation import DATASETS


def test_fixture_windows_intersect_test_geometry_and_reject_far_away() -> None:
    assert _intersects_any((139.58, 35.44, 139.60, 35.46))  # Yokohama window
    assert _intersects_any((139.69, 35.68, 139.71, 35.70))  # Tokyo window
    assert _intersects_any((139.76, 35.86, 139.80, 35.90))  # Koshigaya window
    assert not _intersects_any((140.30, 35.40, 140.32, 35.42))  # Mobara: not a fixture window
    assert not _intersects_any((0.0, 0.0, 1.0, 1.0))


def test_build_clips_each_product_to_the_fixture_windows(tmp_path: Path) -> None:
    source = tmp_path / "mlit"
    source.mkdir()
    inside = {"type": "Feature", "geometry": {"type": "Point", "coordinates": [139.59, 35.45]}, "properties": {"keep": True}}
    outside = {"type": "Feature", "geometry": {"type": "Point", "coordinates": [140.30, 35.41]}, "properties": {"keep": False}}
    for dataset in DATASETS:
        (source / dataset.output).write_text(
            json.dumps(
                {
                    "type": "FeatureCollection",
                    "name": dataset.dataset_id,
                    "metadata": {"license": dataset.license, "scope": "test scope"},
                    "features": [inside, outside],
                }
            ),
            encoding="utf-8",
        )
    (source / "metadata.json").write_text(
        json.dumps({"retrieved_at": "2026-07-22T00:00:00Z", "scope": "test scope"}), encoding="utf-8"
    )

    manifest = build(source=source, output=tmp_path / "fixture")

    assert set(manifest["datasets"]) == {dataset.key for dataset in DATASETS}
    assert manifest["windows"].keys() == FIXTURE_WINDOWS.keys()
    for dataset in DATASETS:
        value = json.loads((tmp_path / "fixture" / dataset.output).read_text(encoding="utf-8"))
        assert [feature["properties"] for feature in value["features"]] == [{"keep": True}], dataset.key
        assert value["metadata"]["scope"].startswith("CI fixture windows derived from:"), dataset.key
        assert manifest["datasets"][dataset.key]["feature_count"] == 1
        assert manifest["datasets"][dataset.key]["retrieved_at"] == "2026-07-22T00:00:00Z"


def test_osm_fixture_clips_buildings_through_the_same_windows(tmp_path: Path) -> None:
    source = tmp_path / "kanto_buildings"
    source.mkdir()
    inside = {"type": "Feature", "geometry": {"type": "Point", "coordinates": [139.59, 35.45]}, "properties": {"osm_id": 1}}
    outside = {"type": "Feature", "geometry": {"type": "Point", "coordinates": [140.30, 35.41]}, "properties": {"osm_id": 2}}
    (source / "buildings.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "name": "osm-test", "metadata": {"license": "ODbL", "scope": "test scope"}, "features": [inside, outside]}),
        encoding="utf-8",
    )
    (source / "metadata.json").write_text(
        json.dumps({"retrieved_at": "2026-07-23T00:00:00Z", "scope": "test scope", "dataset_id": "osm-test", "source_updated_at": "2026-01-01", "license": "ODbL"}),
        encoding="utf-8",
    )

    manifest = build_osm_buildings(source=source, output=tmp_path / "fixture")

    value = json.loads((tmp_path / "fixture/buildings.geojson").read_text(encoding="utf-8"))
    assert [feature["properties"]["osm_id"] for feature in value["features"]] == [1]
    assert value["metadata"]["scope"].startswith("CI fixture windows derived from:")
    assert manifest["feature_count"] == 1
    assert manifest["dataset_id"] == "osm-test"
    assert manifest["windows"].keys() == OSM_FIXTURE_WINDOWS.keys()
