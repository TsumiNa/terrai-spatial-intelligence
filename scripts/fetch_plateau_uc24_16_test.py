from __future__ import annotations

import base64
import json
import struct
import zipfile
from pathlib import Path

import pytest

from scripts.fetch_plateau_uc24_16 import extract_archive, fetch_uc24_16, inspect_tileset


RESOURCE_ID = "bbd1e7cc-4b9e-4438-8127-95a31c7779e2"


def data_uri(value: bytes) -> str:
    return "data:application/octet-stream;base64," + base64.b64encode(value).decode("ascii")


def string_property(values: list[str], buffers: list[dict], views: list[dict]) -> dict[str, int]:
    encoded = [value.encode("utf-8") for value in values]
    offsets = [0]
    for value in encoded:
        offsets.append(offsets[-1] + len(value))
    values_index = len(buffers)
    buffers.append({"uri": data_uri(b"".join(encoded)), "byteLength": offsets[-1]})
    views.append({"buffer": values_index, "byteOffset": 0, "byteLength": offsets[-1]})
    offsets_index = len(buffers)
    offset_bytes = struct.pack(f"<{len(offsets)}I", *offsets)
    buffers.append({"uri": data_uri(offset_bytes), "byteLength": len(offset_bytes)})
    views.append({"buffer": offsets_index, "byteOffset": 0, "byteLength": len(offset_bytes)})
    return {"values": len(views) - 2, "stringOffsets": len(views) - 1}


def gltf_document(*, malformed_metadata: bool = False) -> dict:
    buffers: list[dict] = []
    views: list[dict] = []
    properties = {
        "uro:id": string_property(["feature-1"], buffers, views),
        "uro:minDepth": string_property(["0.5"], buffers, views),
        "uro:outerDiamiter": string_property(["100.0"], buffers, views),
        "uro:mesureType": string_property(["surveyed"], buffers, views),
    }
    metadata = {
        "schema": {
            "classes": {
                "Metadataclass": {
                    "properties": {name: {"type": "STRING"} for name in properties}
                }
            }
        },
        "propertyTables": [
            {"class": "Metadataclass", "count": 1, "properties": properties}
        ],
    }
    if malformed_metadata:
        metadata["propertyTables"][0]["properties"]["uro:id"]["values"] = 999
    return {
        "asset": {"version": "2.0"},
        "extensionsUsed": ["EXT_structural_metadata"],
        "extensions": {"EXT_structural_metadata": metadata},
        "buffers": buffers,
        "bufferViews": views,
    }


def tileset_document(*, content_uri: str = "data/tile.gltf", include_region: bool = True) -> dict:
    root: dict = {
        "geometricError": 1,
        "refine": "REPLACE",
        "content": {"uri": content_uri},
    }
    if include_region:
        root["boundingVolume"] = {"region": [2.43, 0.62, 2.44, 0.63, 1.0, 9.0]}
    return {"asset": {"version": "1.1"}, "geometricError": 1, "root": root}


def make_archive(
    path: Path,
    *,
    tileset: dict | None = None,
    gltf: dict | None = None,
    unsafe_name: str | None = None,
) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        if unsafe_name:
            archive.writestr(unsafe_name, b"unsafe")
        if tileset is not None:
            archive.writestr("tileset.json", json.dumps(tileset))
        if gltf is not None:
            archive.writestr("data/tile.gltf", json.dumps(gltf))


def test_extract_archive_rejects_path_traversal(tmp_path: Path) -> None:
    archive = tmp_path / "unsafe.zip"
    make_archive(archive, unsafe_name="../escape.txt")

    with pytest.raises(RuntimeError, match="unsafe ZIP member"):
        extract_archive(archive, tmp_path / "out")

    assert not (tmp_path / "escape.txt").exists()


def test_extract_archive_requires_one_tileset(tmp_path: Path) -> None:
    archive = tmp_path / "missing.zip"
    make_archive(archive, gltf=gltf_document())

    with pytest.raises(RuntimeError, match="exactly one tileset.json"):
        extract_archive(archive, tmp_path / "out")


def test_inspect_tileset_rejects_a_broken_content_uri(tmp_path: Path) -> None:
    (tmp_path / "tileset.json").write_text(
        json.dumps(tileset_document(content_uri="data/missing.gltf")), encoding="utf-8"
    )

    with pytest.raises(RuntimeError, match="missing tile content"):
        inspect_tileset(tmp_path, resource_id=RESOURCE_ID, utility_class="water_pipe")


def test_inspect_tileset_requires_region_height_metadata(tmp_path: Path) -> None:
    (tmp_path / "data").mkdir()
    (tmp_path / "data/tile.gltf").write_text(json.dumps(gltf_document()), encoding="utf-8")
    (tmp_path / "tileset.json").write_text(
        json.dumps(tileset_document(include_region=False)), encoding="utf-8"
    )

    with pytest.raises(RuntimeError, match="boundingVolume.region"):
        inspect_tileset(tmp_path, resource_id=RESOURCE_ID, utility_class="water_pipe")


def test_inspect_tileset_rejects_malformed_structural_metadata(tmp_path: Path) -> None:
    (tmp_path / "data").mkdir()
    (tmp_path / "data/tile.gltf").write_text(
        json.dumps(gltf_document(malformed_metadata=True)), encoding="utf-8"
    )
    (tmp_path / "tileset.json").write_text(json.dumps(tileset_document()), encoding="utf-8")

    with pytest.raises(RuntimeError, match="bufferView"):
        inspect_tileset(tmp_path, resource_id=RESOURCE_ID, utility_class="water_pipe")


def test_fetch_records_exact_upstream_keys_and_rejects_partial_offline_cache(tmp_path: Path) -> None:
    source = tmp_path / "source.zip"
    make_archive(source, tileset=tileset_document(), gltf=gltf_document())
    source_manifest = tmp_path / "source_manifest.json"
    source_manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "package_id": "plateau-uc24-16",
                "package_api": (tmp_path / "package.json").as_uri(),
                "package_page": "https://example.test/uc24-16",
                "license_url": "https://example.test/licence",
                "resources": [
                    {
                        "resource_id": RESOURCE_ID,
                        "slug": "water-pipe",
                        "utility_class": "water_pipe",
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
                    "metadata_modified": "2025-04-23T00:00:00",
                    "license_title": "PLATEAU Site Policy",
                    "resources": [
                        {
                            "id": RESOURCE_ID,
                            "name": "Nihonbashi water pipe",
                            "url": source.as_uri(),
                            "format": "3d tiles",
                        }
                    ],
                },
            }
        ),
        encoding="utf-8",
    )

    result = fetch_uc24_16(
        root=tmp_path,
        source_manifest_path=source_manifest,
        force=True,
    )

    audit = json.loads((tmp_path / "data/plateau/uc24_16_nihonbashi/audit_index.json").read_text())
    assert result["feature_count"] == 1
    assert audit["features"][0]["source_feature_id"] == "feature-1"
    assert audit["features"][0]["attributes"]["uro:outerDiamiter"] == "100.0"
    assert audit["features"][0]["attributes"]["uro:mesureType"] == "surveyed"
    assert audit["attribute_units"]["uro:outerDiamiter"] is None
    assert "explicitly unknown" in audit["missing_value_semantics"]
    assert result["resources"][0]["tileset_url"].startswith("/api/v1/assets/")

    cached_archive = tmp_path / result["resources"][0]["archive_path"]
    cached_archive.write_bytes(b"corrupt local archive")
    repaired = fetch_uc24_16(root=tmp_path, source_manifest_path=source_manifest)
    assert repaired["resources"][0]["retrieval"] == "official download"
    assert cached_archive.read_bytes() == source.read_bytes()

    (tmp_path / result["resources"][0]["tileset_path"]).unlink()
    with pytest.raises(RuntimeError, match="offline cache is incomplete"):
        fetch_uc24_16(root=tmp_path, source_manifest_path=source_manifest, offline=True)
