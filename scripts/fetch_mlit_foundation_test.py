import json
from pathlib import Path

from scripts.fetch_mlit_foundation import _bbox_in_crs, _json_value, _layers


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
