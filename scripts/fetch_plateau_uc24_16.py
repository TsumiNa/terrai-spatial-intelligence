"""Acquire and audit the PLATEAU UC24-16 Nihonbashi utility sample."""

from __future__ import annotations

import argparse
import base64
import json
import math
import os
import shutil
import struct
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from terrai_spatial.pipeline.http import download_file, download_json  # noqa: E402
from terrai_spatial.pipeline.io import (  # noqa: E402
    file_sha256,
    read_json_object,
    safe_extract_zip,
    safe_relative_path,
    serialize_json,
    write_json_atomic,
    write_text_atomic,
)
from terrai_spatial.pipeline.provenance import utc_timestamp  # noqa: E402

DEFAULT_SOURCE_MANIFEST = ROOT / "data/plateau/uc24_16_nihonbashi/source_manifest.json"
OUTPUT_DIRECTORY = Path("data/plateau/uc24_16_nihonbashi")
CACHE_DIRECTORY = Path("data/external/plateau_uc24_16")
AUDIT_FIELDS = (
    "埋設物の概要",
    "gml:name",
    "core:creationDate",
    "frn:function",
    "uro:id",
    "uro:class",
    "uro:function",
    "uro:occupierType",
    "uro:occupierName",
    "uro:year",
    "uro:yearType",
    "uro:administrator",
    "uro:minDepth",
    "uro:maxDepth",
    "uro:maxWidth",
    "uro:material",
    "uro:length",
    "uro:mesureType",
    "uro:phaseType",
    "uro:outerDiamiter",
    "uro:geometrySrcDescLod1",
    "uro:geometrySrcDescLod2",
    "uro:thematicSrcDesc",
)


def _atomic_audit_json(path: Path, metadata: dict[str, Any], records: list[dict[str, Any]]) -> None:
    """Keep the complete audit index compact while retaining reviewable rows."""

    prefix = serialize_json({**metadata, "features": []})
    prefix = prefix.replace('"features": []', '"features": [', 1).removesuffix("\n}")
    parts = [prefix, "\n"]
    for index, record in enumerate(records):
        parts.append("    ")
        parts.append(json.dumps(record, ensure_ascii=False, separators=(",", ":")))
        parts.append(",\n" if index + 1 < len(records) else "\n")
    parts.append("  ]\n}\n")
    write_text_atomic(path, "".join(parts))


def extract_archive(archive_path: Path, destination: Path) -> Path:
    """Safely extract an archive and return its single tileset directory."""

    safe_extract_zip(archive_path, destination)
    tilesets = sorted(destination.rglob("tileset.json"))
    if len(tilesets) != 1:
        raise RuntimeError(f"archive must contain exactly one tileset.json; found {len(tilesets)}")
    return tilesets[0].parent


def _local_uri(base: Path, uri: str, root: Path) -> Path:
    parsed = urlsplit(uri)
    if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
        raise RuntimeError(f"tile content URI must be a local relative path: {uri!r}")
    relative = safe_relative_path(parsed.path, label="tile content URI")
    path = base.joinpath(*relative.parts).resolve()
    root_resolved = root.resolve()
    if path != root_resolved and root_resolved not in path.parents:
        raise RuntimeError(f"tile content URI escapes the asset root: {uri!r}")
    return path


def _tile_content_paths(node: dict[str, Any], *, tileset_dir: Path, asset_root: Path) -> list[Path]:
    paths: list[Path] = []
    contents: list[Any] = []
    if "content" in node:
        contents.append(node["content"])
    contents.extend(node.get("contents", []))
    for content in contents:
        if not isinstance(content, dict) or not isinstance(content.get("uri"), str):
            raise RuntimeError("tile content is missing a string URI")
        path = _local_uri(tileset_dir, content["uri"], asset_root)
        if not path.is_file():
            raise RuntimeError(f"missing tile content: {content['uri']}")
        paths.append(path)
    for child in node.get("children", []):
        if not isinstance(child, dict):
            raise RuntimeError("tileset child is not an object")
        paths.extend(_tile_content_paths(child, tileset_dir=tileset_dir, asset_root=asset_root))
    return paths


def _buffer_bytes(document: dict[str, Any], index: int, gltf_path: Path, asset_root: Path) -> bytes:
    buffers = document.get("buffers", [])
    if not isinstance(index, int) or index < 0 or index >= len(buffers):
        raise RuntimeError(f"structural metadata references invalid buffer {index}")
    buffer = buffers[index]
    uri = buffer.get("uri")
    if not isinstance(uri, str):
        raise RuntimeError(f"glTF buffer {index} has no URI")
    if uri.startswith("data:"):
        try:
            header, encoded = uri.split(",", 1)
            if ";base64" not in header:
                raise ValueError("not base64")
            value = base64.b64decode(encoded, validate=True)
        except (ValueError, base64.binascii.Error) as error:
            raise RuntimeError(f"invalid data URI in glTF buffer {index}") from error
    else:
        value = _local_uri(gltf_path.parent, uri, asset_root).read_bytes()
    declared = buffer.get("byteLength")
    if not isinstance(declared, int) or declared < 0 or len(value) < declared:
        raise RuntimeError(f"glTF buffer {index} is shorter than byteLength")
    return value


def _buffer_view(document: dict[str, Any], index: Any, gltf_path: Path, asset_root: Path) -> bytes:
    views = document.get("bufferViews", [])
    if not isinstance(index, int) or index < 0 or index >= len(views):
        raise RuntimeError(f"structural metadata references invalid bufferView {index}")
    view = views[index]
    buffer = _buffer_bytes(document, view.get("buffer"), gltf_path, asset_root)
    offset = view.get("byteOffset", 0)
    length = view.get("byteLength")
    if not isinstance(offset, int) or not isinstance(length, int) or offset < 0 or length < 0:
        raise RuntimeError(f"invalid structural metadata bufferView {index}")
    if offset + length > len(buffer):
        raise RuntimeError(f"structural metadata bufferView {index} exceeds its buffer")
    return buffer[offset : offset + length]


def _strings(
    document: dict[str, Any],
    property_value: dict[str, Any],
    count: int,
    gltf_path: Path,
    asset_root: Path,
) -> list[str]:
    values = _buffer_view(document, property_value.get("values"), gltf_path, asset_root)
    offsets = _buffer_view(document, property_value.get("stringOffsets"), gltf_path, asset_root)
    offset_type = property_value.get("stringOffsetType", "UINT32")
    formats = {"UINT8": "B", "UINT16": "H", "UINT32": "I", "UINT64": "Q"}
    try:
        item_format = formats[offset_type]
    except KeyError as error:
        raise RuntimeError(f"unsupported stringOffsetType: {offset_type}") from error
    item_size = struct.calcsize(item_format)
    expected = (count + 1) * item_size
    if len(offsets) != expected:
        raise RuntimeError(f"string offsets have {len(offsets)} bytes; expected {expected}")
    positions = struct.unpack(f"<{count + 1}{item_format}", offsets)
    if positions[0] != 0 or positions[-1] != len(values) or list(positions) != sorted(positions):
        raise RuntimeError("string offsets do not describe the values buffer")
    try:
        return [values[positions[index] : positions[index + 1]].decode("utf-8") for index in range(count)]
    except UnicodeDecodeError as error:
        raise RuntimeError("structural metadata string is not UTF-8") from error


def _gltf_records(
    gltf_path: Path,
    *,
    asset_root: Path,
    resource_id: str,
    utility_class: str,
) -> tuple[list[dict[str, Any]], set[str]]:
    document = read_json_object(gltf_path, label="glTF")
    metadata = document.get("extensions", {}).get("EXT_structural_metadata")
    if "EXT_structural_metadata" not in document.get("extensionsUsed", []) or not isinstance(metadata, dict):
        raise RuntimeError(f"glTF lacks EXT_structural_metadata: {gltf_path.name}")
    tables = metadata.get("propertyTables")
    classes = metadata.get("schema", {}).get("classes", {})
    if not isinstance(tables, list) or not tables:
        raise RuntimeError(f"glTF has no structural metadata property table: {gltf_path.name}")

    records: list[dict[str, Any]] = []
    observed_fields: set[str] = set()
    relative_gltf = gltf_path.relative_to(asset_root).as_posix()
    for table_index, table in enumerate(tables):
        count = table.get("count")
        properties = table.get("properties")
        class_properties = classes.get(table.get("class"), {}).get("properties", {})
        if not isinstance(count, int) or count < 0 or not isinstance(properties, dict):
            raise RuntimeError(f"malformed structural metadata property table: {gltf_path.name}")
        decoded: dict[str, list[str]] = {}
        for name in AUDIT_FIELDS:
            if name not in properties:
                continue
            if class_properties.get(name, {}).get("type") != "STRING":
                raise RuntimeError(f"unsupported non-string audit field {name}: {gltf_path.name}")
            decoded[name] = _strings(document, properties[name], count, gltf_path, asset_root)
            observed_fields.add(name)
        for row in range(count):
            attributes = {name: (values[row] or None) for name, values in decoded.items()}
            source_id = attributes.get("uro:id")
            records.append(
                {
                    "record_id": f"{resource_id}:{relative_gltf}:{table_index}:{row}",
                    "source_feature_id": source_id,
                    "source_resource_id": resource_id,
                    "source_asset": relative_gltf,
                    "utility_class": utility_class,
                    "attributes": attributes,
                }
            )
    return records, observed_fields


def inspect_tileset(
    asset_root: Path,
    *,
    resource_id: str,
    utility_class: str,
) -> dict[str, Any]:
    tilesets = sorted(asset_root.rglob("tileset.json"))
    if len(tilesets) != 1:
        raise RuntimeError(f"asset must contain exactly one tileset.json; found {len(tilesets)}")
    tileset_path = tilesets[0]
    document = read_json_object(tileset_path, label="3D Tiles tileset")
    if document.get("asset", {}).get("version") != "1.1":
        raise RuntimeError("3D Tiles asset.version must be 1.1")
    root_tile = document.get("root")
    if not isinstance(root_tile, dict):
        raise RuntimeError("3D Tiles root is missing")
    region = root_tile.get("boundingVolume", {}).get("region")
    if (
        not isinstance(region, list)
        or len(region) != 6
        or not all(isinstance(value, (int, float)) and math.isfinite(value) for value in region)
    ):
        raise RuntimeError("3D Tiles root must provide a six-value boundingVolume.region")
    if region[0] > region[2] or region[1] > region[3] or region[4] > region[5]:
        raise RuntimeError("3D Tiles boundingVolume.region has reversed bounds")

    contents = _tile_content_paths(root_tile, tileset_dir=tileset_path.parent, asset_root=asset_root)
    if not contents:
        raise RuntimeError("3D Tiles tileset contains no content")
    records: list[dict[str, Any]] = []
    observed_fields: set[str] = set()
    for content in sorted(set(contents)):
        if content.suffix.lower() != ".gltf":
            raise RuntimeError(f"unsupported tile content type: {content.name}")
        file_records, fields = _gltf_records(
            content,
            asset_root=asset_root,
            resource_id=resource_id,
            utility_class=utility_class,
        )
        records.extend(file_records)
        observed_fields.update(fields)

    return {
        "tileset_relative": tileset_path.relative_to(asset_root).as_posix(),
        "gltf_count": len(set(contents)),
        "feature_count": len(records),
        "observed_fields": sorted(observed_fields),
        "bounding_region": {
            "radians": region,
            "degrees_and_metres": [
                math.degrees(region[0]),
                math.degrees(region[1]),
                math.degrees(region[2]),
                math.degrees(region[3]),
                region[4],
                region[5],
            ],
        },
        "records": records,
    }


def _relative(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _asset_url(relative: str) -> str:
    if not relative.startswith("data/"):
        raise RuntimeError(f"asset is outside the mounted data directory: {relative}")
    return "/api/v1/assets/" + relative.removeprefix("data/")


def _validate_offline(root: Path, manifest_path: Path) -> dict[str, Any]:
    if not manifest_path.is_file():
        raise RuntimeError("offline cache is incomplete: retrieval manifest is missing")
    manifest = read_json_object(manifest_path, label="UC24-16 retrieval manifest")
    missing = [relative for relative in manifest.get("files", []) if not (root / relative).is_file()]
    if missing:
        raise RuntimeError(f"offline cache is incomplete: missing {', '.join(missing[:3])}")
    for resource in manifest.get("resources", []):
        archive = root / resource["archive_path"]
        if file_sha256(archive) != resource["archive_sha256"]:
            raise RuntimeError(f"offline cache archive hash mismatch: {resource['slug']}")
        tileset = root / resource["tileset_path"]
        inspect_tileset(
            tileset.parent,
            resource_id=resource["resource_id"],
            utility_class=resource["utility_class"],
        )
    return manifest


def fetch_uc24_16(
    *,
    root: Path = ROOT,
    source_manifest_path: Path = DEFAULT_SOURCE_MANIFEST,
    force: bool = False,
    offline: bool = False,
) -> dict[str, Any]:
    output_dir = root / OUTPUT_DIRECTORY
    cache_dir = root / CACHE_DIRECTORY
    retrieval_manifest_path = output_dir / "manifest.json"
    if offline:
        return _validate_offline(root, retrieval_manifest_path)

    source_manifest = read_json_object(source_manifest_path, label="UC24-16 source manifest")
    package, package_headers = download_json(source_manifest["package_api"], timeout=120)
    if not isinstance(package, dict) or package.get("success") is not True or not isinstance(package.get("result"), dict):
        raise RuntimeError("official CKAN package_show request was not successful")
    package_result = package["result"]
    resources_by_id = {resource.get("id"): resource for resource in package_result.get("resources", [])}
    previous = read_json_object(retrieval_manifest_path, label="UC24-16 retrieval manifest") if retrieval_manifest_path.is_file() else {}
    previous_by_id = {resource["resource_id"]: resource for resource in previous.get("resources", [])}
    retrieved_at = utc_timestamp()
    archive_dir = cache_dir / "archives"
    assets_dir = cache_dir / "assets"
    archive_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    manifest_resources: list[dict[str, Any]] = []
    audit_records: list[dict[str, Any]] = []
    all_files: list[str] = []
    observed_fields: set[str] = set()
    for selection in source_manifest.get("resources", []):
        resource_id = selection["resource_id"]
        try:
            official = resources_by_id[resource_id]
        except KeyError as error:
            raise RuntimeError(f"selected UC24-16 resource is missing from CKAN: {resource_id}") from error
        if not isinstance(official.get("url"), str):
            raise RuntimeError(f"selected UC24-16 resource has no download URL: {resource_id}")

        slug = selection["slug"]
        archive_path = archive_dir / f"{slug}.zip"
        asset_directory = assets_dir / slug
        prior = previous_by_id.get(resource_id, {})
        cached_inspection: dict[str, Any] | None = None
        if not force and archive_path.is_file() and asset_directory.is_dir():
            try:
                cached_inspection = inspect_tileset(
                    asset_directory,
                    resource_id=resource_id,
                    utility_class=selection["utility_class"],
                )
            except RuntimeError:
                cached_inspection = None
            expected_archive_hash = prior.get("archive_sha256")
            if expected_archive_hash and file_sha256(archive_path) != expected_archive_hash:
                cached_inspection = None

        download_headers: dict[str, str | None]
        if cached_inspection is None:
            with tempfile.NamedTemporaryFile("wb", dir=cache_dir, delete=False) as handle:
                temporary_archive = Path(handle.name)
            try:
                download_headers = download_file(official["url"], temporary_archive, timeout=300)
                if not zipfile.is_zipfile(temporary_archive):
                    raise RuntimeError(f"UC24-16 resource is not a ZIP archive: {slug}")
                with tempfile.TemporaryDirectory(dir=cache_dir) as temporary_directory:
                    staging = Path(temporary_directory)
                    extract_archive(temporary_archive, staging)
                    inspection = inspect_tileset(
                        staging,
                        resource_id=resource_id,
                        utility_class=selection["utility_class"],
                    )
                    if asset_directory.exists():
                        shutil.rmtree(asset_directory)
                    shutil.move(staging, asset_directory)
                os.replace(temporary_archive, archive_path)
            finally:
                temporary_archive.unlink(missing_ok=True)
            retrieval = "official download"
            resource_retrieved_at = retrieved_at
        else:
            inspection = cached_inspection
            download_headers = {
                "resolved_url": prior.get("resolved_url", official["url"]),
                "http_last_modified": prior.get("http_last_modified"),
                "http_etag": prior.get("http_etag"),
            }
            retrieval = "existing local cache"
            resource_retrieved_at = prior.get("retrieved_at", retrieved_at)

        archive_relative = _relative(root, archive_path)
        tileset_path = asset_directory / inspection["tileset_relative"]
        tileset_relative = _relative(root, tileset_path)
        asset_files = sorted(_relative(root, path) for path in asset_directory.rglob("*") if path.is_file())
        all_files.extend([archive_relative, *asset_files])
        audit_records.extend(inspection.pop("records"))
        observed_fields.update(inspection["observed_fields"])
        manifest_resources.append(
            {
                "resource_id": resource_id,
                "slug": slug,
                "utility_class": selection["utility_class"],
                "name": official.get("name"),
                "format": official.get("format"),
                "download_url": official["url"],
                "resolved_url": download_headers["resolved_url"],
                "retrieved_at": resource_retrieved_at,
                "retrieval": retrieval,
                "http_last_modified": download_headers["http_last_modified"],
                "http_etag": download_headers["http_etag"],
                "archive_path": archive_relative,
                "archive_bytes": archive_path.stat().st_size,
                "archive_sha256": file_sha256(archive_path),
                "tileset_path": tileset_relative,
                "tileset_url": _asset_url(tileset_relative),
                **inspection,
            }
        )

    audit_records.sort(key=lambda row: row["record_id"])
    west = min(resource["bounding_region"]["degrees_and_metres"][0] for resource in manifest_resources)
    south = min(resource["bounding_region"]["degrees_and_metres"][1] for resource in manifest_resources)
    east = max(resource["bounding_region"]["degrees_and_metres"][2] for resource in manifest_resources)
    north = max(resource["bounding_region"]["degrees_and_metres"][3] for resource in manifest_resources)
    minimum_height = min(resource["bounding_region"]["degrees_and_metres"][4] for resource in manifest_resources)
    maximum_height = max(resource["bounding_region"]["degrees_and_metres"][5] for resource in manifest_resources)
    manifest = {
        "schema_version": 1,
        "dataset_id": "plateau_uc24_16_nihonbashi",
        "scene_id": "nihonbashi-utilities",
        "evidence_status": "observed_external_sample",
        "package_id": source_manifest["package_id"],
        "package_api": source_manifest["package_api"],
        "package_page": source_manifest["package_page"],
        "package_metadata_modified": package_result.get("metadata_modified"),
        "package_resolved_url": package_headers["resolved_url"],
        "retrieved_at": retrieved_at,
        "license": package_result.get("license_title") or "PLATEAU Site Policy",
        "license_url": source_manifest["license_url"],
        "horizontal_crs": "EPSG:4326 longitude/latitude encoded as 3D Tiles region radians",
        "height_unit": "metre",
        "height_reference": "WGS 84 ellipsoid per 3D Tiles boundingVolume.region semantics",
        "vertical_datum": "WGS 84 ellipsoid (not an orthometric survey datum)",
        "depth_semantics": "uro:minDepth and uro:maxDepth are source attributes and are not subtracted from absolute tile height; their units are not encoded in the glTF property table",
        "extent_degrees_and_metres": [west, south, east, north, minimum_height, maximum_height],
        "feature_count": len(audit_records),
        "resource_count": len(manifest_resources),
        "observed_fields": sorted(observed_fields),
        "files": sorted(set(all_files)),
        "resources": manifest_resources,
        "limitations": [
            "2024 demonstration data for a limited Nihonbashi sample, not an operational utility ledger",
            "not suitable for excavation, engineering design, emergency response or asset-condition decisions",
            "communications assets are not classified as optical fibre unless an upstream attribute says so",
        ],
    }
    audit_metadata = {
        "schema_version": 1,
        "dataset_id": manifest["dataset_id"],
        "generated_at": retrieved_at,
        "feature_count": len(audit_records),
        "attribute_keys": sorted(observed_fields),
        "source_key_note": "uro:outerDiamiter and uro:mesureType are exact upstream spellings",
        "missing_value_semantics": "an omitted attribute key is explicitly unknown because the source property table did not publish it for that feature class",
        "attribute_units": {
            "uro:minDepth": None,
            "uro:maxDepth": None,
            "uro:outerDiamiter": None,
            "uro:length": None,
        },
        "unit_note": "source glTF structural metadata does not encode units for depth, diameter or length",
    }
    _atomic_audit_json(output_dir / "audit_index.json", audit_metadata, audit_records)
    write_json_atomic(retrieval_manifest_path, manifest)
    print(
        f"UC24-16 Nihonbashi cache ready: {len(manifest_resources)} resources, "
        f"{len(audit_records)} features"
    )
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="refresh every selected archive from official URLs")
    parser.add_argument("--offline", action="store_true", help="validate only an existing complete local cache")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    fetch_uc24_16(force=args.force, offline=args.offline)


if __name__ == "__main__":
    main()
