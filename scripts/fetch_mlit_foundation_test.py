import json
from pathlib import Path

from scripts.fetch_mlit_foundation import (
    CONTEXTS,
    DATASETS,
    PREFECTURES,
    StreamedCollection,
    _bbox_in_crs,
    _json_value,
    _layers,
)
from terrai_spatial.pipeline.io import write_json_atomic


def test_preferred_layer_avoids_duplicate_shapefile(tmp_path: Path) -> None:
    (tmp_path / "data.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": []}))
    (tmp_path / "data.shp").touch()
    assert _layers(tmp_path, "preferred") == [tmp_path / "data.geojson"]


def test_json_value_normalizes_non_json_values() -> None:
    assert _json_value(b"abc") == "abc"


def test_bbox_is_transformed_to_projected_source_crs() -> None:
    bbox = _bbox_in_crs((139.5, 35.4, 139.6, 35.5), "EPSG:3857")
    assert bbox[0] > 15_000_000
    assert bbox[1] > 4_000_000
    assert bbox[2] > bbox[0]
    assert bbox[3] > bbox[1]


def test_every_archive_is_an_nlftp_url_with_a_known_window() -> None:
    for dataset in DATASETS:
        assert dataset.archives, dataset.key
        for archive in dataset.archives:
            assert archive.url.startswith("https://nlftp.mlit.go.jp/"), archive.url
            assert archive.region in CONTEXTS, archive.url


def test_per_prefecture_datasets_cover_all_four_prefectures() -> None:
    table = {dataset.key: dataset for dataset in DATASETS}
    for key in ("landslideWarning", "publishedLandPrice", "embankmentRegulation", "prefecturalLandPrice"):
        codes = tuple(Path(archive.url).name.split("_")[1] for archive in table[key].archives)
        assert codes == PREFECTURES, key


def test_only_mesh_5238_is_clipped_to_the_hakone_west_window() -> None:
    table = {dataset.key: dataset for dataset in DATASETS}
    for archive in table["landUseMesh"].archives:
        expected = "hakone_west" if "_5238-" in archive.url else "kanto"
        assert archive.region == expected, archive.url


def test_streamed_collection_matches_the_atomic_writer_byte_for_byte(tmp_path: Path) -> None:
    metadata = {"license": "CC BY 4.0", "scope": "テスト"}
    features = [
        {"type": "Feature", "geometry": {"type": "Point", "coordinates": [139.5, 35.4]}, "properties": {"名称": "駅", "n": 1}},
        {"type": "Feature", "geometry": None, "properties": {"n": 2}},
    ]
    streamed = StreamedCollection(tmp_path / "streamed.geojson", "ksj-test", metadata)
    for feature in features:
        streamed.add(feature)
    streamed.close()
    write_json_atomic(
        tmp_path / "reference.geojson",
        {"type": "FeatureCollection", "name": "ksj-test", "metadata": metadata, "features": features},
        compact=True,
        trailing_newline=False,
    )
    assert (tmp_path / "streamed.geojson").read_bytes() == (tmp_path / "reference.geojson").read_bytes()


def test_streamed_collection_with_no_features_is_a_valid_empty_collection(tmp_path: Path) -> None:
    streamed = StreamedCollection(tmp_path / "empty.geojson", "ksj-test", {})
    streamed.close()
    value = json.loads((tmp_path / "empty.geojson").read_text(encoding="utf-8"))
    assert value["type"] == "FeatureCollection"
    assert value["features"] == []
    assert streamed.count == 0


def test_discard_removes_the_partial_file(tmp_path: Path) -> None:
    streamed = StreamedCollection(tmp_path / "partial.geojson", "ksj-test", {})
    streamed.add({"type": "Feature", "geometry": None, "properties": {}})
    streamed.discard()
    assert list(tmp_path.iterdir()) == []


def test_concurrent_writers_to_the_same_target_do_not_interleave(tmp_path: Path) -> None:
    # Two overlapping builds (an ensure-triggered fetch beside a manual one)
    # must each write their own temporary file; the last to close wins whole.
    first = StreamedCollection(tmp_path / "same.geojson", "ksj-test", {"round": 1})
    second = StreamedCollection(tmp_path / "same.geojson", "ksj-test", {"round": 2})
    first.add({"type": "Feature", "geometry": None, "properties": {"from": "first"}})
    second.add({"type": "Feature", "geometry": None, "properties": {"from": "second"}})
    first.close()
    second.close()

    value = json.loads((tmp_path / "same.geojson").read_text(encoding="utf-8"))
    assert value["metadata"] == {"round": 2}
    assert value["features"][0]["properties"] == {"from": "second"}
    assert sorted(item.name for item in tmp_path.iterdir()) == ["same.geojson"]
