import json
import zipfile
from pathlib import Path

import pytest

from scripts.fetch_mlit_foundation import _extract, _json_value, _layers


def test_extract_rejects_path_traversal(tmp_path: Path) -> None:
    archive = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(archive, "w") as zipped:
        zipped.writestr("../escape.txt", "bad")
    with pytest.raises(ValueError, match="unsafe ZIP member"):
        _extract(archive, tmp_path / "out")


def test_preferred_layer_avoids_duplicate_shapefile(tmp_path: Path) -> None:
    (tmp_path / "data.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": []}))
    (tmp_path / "data.shp").touch()
    assert _layers(tmp_path, "preferred") == [tmp_path / "data.geojson"]


def test_json_value_normalizes_non_json_values() -> None:
    assert _json_value(b"abc") == "abc"
