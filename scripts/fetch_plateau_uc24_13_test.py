from __future__ import annotations

import json
import struct
import zipfile
from pathlib import Path

import pytest

from scripts.fetch_plateau_uc24_13 import fetch_uc24_13, inspect_b3dm, inspect_tileset


RESOURCE_ID = "b0d1e3b0-4137-47c0-b975-9410a92801fe"


def b3dm_document(*, batch_length: int = 1, declared_delta: int = 0) -> bytes:
    feature_table = json.dumps({"BATCH_LENGTH": batch_length}, separators=(",", ":")).encode()
    batch_table = json.dumps(
        {
            "gml_id": [f"feature-{index}" for index in range(batch_length)],
            "feature_type": ["uro:UndergroundBuilding"] * batch_length,
            "city_code": ["01100"] * batch_length,
        },
        separators=(",", ":"),
    ).encode()
    glb = b"glTF" + b"\x00" * 8
    byte_length = 28 + len(feature_table) + len(batch_table) + len(glb)
    header = struct.pack(
        "<4s6I",
        b"b3dm",
        1,
        byte_length + declared_delta,
        len(feature_table),
        0,
        len(batch_table),
        0,
    )
    return header + feature_table + batch_table + glb


def tileset_document(*, content_uri: str = "data/tile.b3dm") -> dict:
    return {
        "asset": {"version": "1.0"},
        "geometricError": 1,
        "root": {
            "boundingVolume": {"region": [2.46, 0.75, 2.47, 0.76, 30.0, 60.0]},
            "geometricError": 0,
            "content": {"uri": content_uri},
        },
    }


def make_archive(path: Path, *, broken_length: bool = False) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("tileset.json", json.dumps(tileset_document()))
        archive.writestr("data/tile.b3dm", b3dm_document(batch_length=2, declared_delta=1 if broken_length else 0))


def test_inspect_b3dm_rejects_a_mismatched_declared_length(tmp_path: Path) -> None:
    path = tmp_path / "tile.b3dm"
    path.write_bytes(b3dm_document(declared_delta=1))

    with pytest.raises(RuntimeError, match="byteLength"):
        inspect_b3dm(path)


def test_inspect_tileset_counts_batched_source_identities(tmp_path: Path) -> None:
    (tmp_path / "data").mkdir()
    (tmp_path / "tileset.json").write_text(json.dumps(tileset_document()), encoding="utf-8")
    (tmp_path / "data/tile.b3dm").write_bytes(b3dm_document(batch_length=2))

    result = inspect_tileset(tmp_path)

    assert result["content_count"] == 1
    assert result["feature_count"] == 2
    assert result["gml_id_count"] == 2
    assert result["feature_type_counts"] == {"uro:UndergroundBuilding": 2}
    assert result["city_codes"] == ["01100"]


def test_fetch_preserves_reference_inventory_and_rejects_partial_offline_cache(tmp_path: Path) -> None:
    source = tmp_path / "source.zip"
    make_archive(source)
    source_manifest = tmp_path / "source_manifest.json"
    source_manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "dataset_id": "plateau_uc24_13_sapporo",
                "scene_id": "sapporo-station-underground",
                "package_id": "plateau-uc24-13",
                "package_api": (tmp_path / "package.json").as_uri(),
                "package_page": "https://example.test/uc24-13",
                "license_url": "https://example.test/licence",
                "resources": [
                    {
                        "resource_id": RESOURCE_ID,
                        "slug": "sapporo-underground-mall",
                        "structure_class": "underground_mall",
                    }
                ],
                "reference_resources": [
                    {
                        "package_id": "plateau-uc24-13",
                        "resource_id": "reference-id",
                        "label": "reference only",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "package.json").write_text(
        json.dumps(
            {
                "success": True,
                "result": {
                    "metadata_modified": "2025-05-26T09:23:39",
                    "license_title": "PLATEAU Site Policy",
                    "resources": [
                        {"id": RESOURCE_ID, "name": "Sapporo mall", "url": source.as_uri(), "format": "3d tiles"},
                        {
                            "id": "reference-id",
                            "name": "Reference structure",
                            "url": "https://example.test/reference.zip",
                            "format": "3d tiles",
                        },
                    ],
                },
            }
        ),
        encoding="utf-8",
    )

    result = fetch_uc24_13(root=tmp_path, source_manifest_path=source_manifest, force=True)

    assert result["feature_count"] == 2
    assert result["resources"][0]["tileset_url"].startswith("/api/v1/assets/")
    assert result["reference_resources"][0]["status"] == "reference_only"
    assert result["reference_resources"][0]["name"] == "Reference structure"
    assert "no level, depth" in result["missing_value_semantics"]

    (tmp_path / result["resources"][0]["tileset_path"]).unlink()
    with pytest.raises(RuntimeError, match="offline cache is incomplete"):
        fetch_uc24_13(root=tmp_path, source_manifest_path=source_manifest, offline=True)
