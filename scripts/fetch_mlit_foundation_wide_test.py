import json
from pathlib import Path

from scripts.fetch_mlit_foundation import DATASETS as DEMO_DATASETS
from scripts.fetch_mlit_foundation_wide import (
    CONTEXTS,
    PREFECTURES,
    WIDE_DATASETS,
    StreamedCollection,
)
from terrai_spatial.pipeline.io import write_json_atomic


def test_wide_table_mirrors_the_demo_table_per_key() -> None:
    demo = {dataset.key: dataset for dataset in DEMO_DATASETS}
    wide = {dataset.key: dataset for dataset in WIDE_DATASETS}
    assert set(wide) == set(demo)
    for key, dataset in wide.items():
        assert dataset.dataset_id == demo[key].dataset_id, key
        assert dataset.output == demo[key].output, key
        assert dataset.source_updated_at == demo[key].source_updated_at, key
        assert dataset.license == demo[key].license, key
        assert dataset.include == demo[key].include, key


def test_every_archive_is_an_nlftp_url_with_a_known_window() -> None:
    for dataset in WIDE_DATASETS:
        assert dataset.archives, dataset.key
        for archive in dataset.archives:
            assert archive.url.startswith("https://nlftp.mlit.go.jp/"), archive.url
            assert archive.region in CONTEXTS, archive.url


def test_per_prefecture_datasets_cover_all_four_prefectures() -> None:
    wide = {dataset.key: dataset for dataset in WIDE_DATASETS}
    for key in ("landslideWarning", "publishedLandPrice", "embankmentRegulation", "prefecturalLandPrice"):
        codes = tuple(Path(archive.url).name.split("_")[1] for archive in wide[key].archives)
        assert codes == PREFECTURES, key


def test_only_mesh_5238_is_clipped_to_the_hakone_west_window() -> None:
    wide = {dataset.key: dataset for dataset in WIDE_DATASETS}
    for archive in wide["landUseMesh"].archives:
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
