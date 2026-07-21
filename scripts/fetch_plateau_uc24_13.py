"""Acquire and validate the PLATEAU UC24-13 Sapporo underground scene."""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import struct
import tempfile
import zipfile
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

if __package__:
    from .fetch_plateau_uc24_16 import (
        _asset_url,
        _atomic_json,
        _download,
        _json,
        _relative,
        _request_json,
        _tile_content_paths,
        extract_archive,
        sha256,
    )
else:
    from fetch_plateau_uc24_16 import (
        _asset_url,
        _atomic_json,
        _download,
        _json,
        _relative,
        _request_json,
        _tile_content_paths,
        extract_archive,
        sha256,
    )


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_MANIFEST = ROOT / "data/plateau/uc24_13_sapporo/source_manifest.json"
OUTPUT_DIRECTORY = Path("data/plateau/uc24_13_sapporo")
CACHE_DIRECTORY = Path("data/external/plateau_uc24_13")


def _json_section(value: bytes, *, label: str, path: Path) -> dict[str, Any]:
    if not value:
        return {}
    try:
        decoded = json.loads(value.decode("utf-8").strip(" \t\r\n\x00"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError(f"invalid {label} in {path.name}: {error}") from error
    if not isinstance(decoded, dict):
        raise RuntimeError(f"invalid {label} in {path.name}: root is not an object")
    return decoded


def inspect_b3dm(path: Path) -> dict[str, Any]:
    """Validate a legacy B3DM container and summarize its audit attributes."""

    value = path.read_bytes()
    if len(value) < 28:
        raise RuntimeError(f"B3DM header is truncated: {path.name}")
    magic, version, byte_length, feature_json_length, feature_binary_length, batch_json_length, batch_binary_length = struct.unpack(
        "<4s6I", value[:28]
    )
    if magic != b"b3dm" or version != 1:
        raise RuntimeError(f"unsupported B3DM header: {path.name}")
    if byte_length != len(value):
        raise RuntimeError(f"B3DM byteLength does not match the file: {path.name}")
    glb_offset = 28 + feature_json_length + feature_binary_length + batch_json_length + batch_binary_length
    if glb_offset + 4 > len(value) or value[glb_offset : glb_offset + 4] != b"glTF":
        raise RuntimeError(f"B3DM does not contain an embedded GLB: {path.name}")

    feature_start = 28
    feature_table = _json_section(
        value[feature_start : feature_start + feature_json_length],
        label="B3DM feature table JSON",
        path=path,
    )
    batch_start = feature_start + feature_json_length + feature_binary_length
    batch_table = _json_section(
        value[batch_start : batch_start + batch_json_length],
        label="B3DM batch table JSON",
        path=path,
    )
    batch_length = feature_table.get("BATCH_LENGTH")
    if not isinstance(batch_length, int) or batch_length < 0:
        raise RuntimeError(f"B3DM feature table lacks a valid BATCH_LENGTH: {path.name}")
    for name, field in batch_table.items():
        if isinstance(field, list) and len(field) != batch_length:
            raise RuntimeError(f"B3DM batch field {name} has the wrong length: {path.name}")

    feature_types = Counter(
        item for item in batch_table.get("feature_type", []) if isinstance(item, str) and item
    )
    gml_ids = [item for item in batch_table.get("gml_id", []) if isinstance(item, str) and item]
    city_codes = sorted(
        {item for item in batch_table.get("city_code", []) if isinstance(item, str) and item}
    )
    return {
        "feature_count": batch_length,
        "gml_id_count": len(gml_ids),
        "feature_type_counts": dict(sorted(feature_types.items())),
        "city_codes": city_codes,
        "batch_table_fields": sorted(batch_table),
    }


def inspect_tileset(asset_root: Path) -> dict[str, Any]:
    tilesets = sorted(asset_root.rglob("tileset.json"))
    if len(tilesets) != 1:
        raise RuntimeError(f"asset must contain exactly one tileset.json; found {len(tilesets)}")
    tileset_path = tilesets[0]
    document = _json(tileset_path, label="3D Tiles tileset")
    if document.get("asset", {}).get("version") != "1.0":
        raise RuntimeError("UC24-13 3D Tiles asset.version must be 1.0")
    root_tile = document.get("root")
    if not isinstance(root_tile, dict):
        raise RuntimeError("3D Tiles root is missing")
    region = root_tile.get("boundingVolume", {}).get("region")
    if (
        not isinstance(region, list)
        or len(region) != 6
        or not all(isinstance(item, (int, float)) and math.isfinite(item) for item in region)
    ):
        raise RuntimeError("3D Tiles root must provide a six-value boundingVolume.region")
    if region[0] > region[2] or region[1] > region[3] or region[4] > region[5]:
        raise RuntimeError("3D Tiles boundingVolume.region has reversed bounds")

    contents = sorted(set(_tile_content_paths(root_tile, tileset_dir=tileset_path.parent, asset_root=asset_root)))
    if not contents:
        raise RuntimeError("3D Tiles tileset contains no content")
    feature_count = 0
    gml_id_count = 0
    feature_type_counts: Counter[str] = Counter()
    city_codes: set[str] = set()
    batch_table_fields: set[str] = set()
    for content in contents:
        if content.suffix.lower() != ".b3dm":
            raise RuntimeError(f"unsupported UC24-13 tile content type: {content.name}")
        summary = inspect_b3dm(content)
        feature_count += summary["feature_count"]
        gml_id_count += summary["gml_id_count"]
        feature_type_counts.update(summary["feature_type_counts"])
        city_codes.update(summary["city_codes"])
        batch_table_fields.update(summary["batch_table_fields"])

    return {
        "tileset_relative": tileset_path.relative_to(asset_root).as_posix(),
        "content_count": len(contents),
        "feature_count": feature_count,
        "gml_id_count": gml_id_count,
        "feature_type_counts": dict(sorted(feature_type_counts.items())),
        "city_codes": sorted(city_codes),
        "batch_table_fields": sorted(batch_table_fields),
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
    }


def _validate_offline(root: Path, manifest_path: Path) -> dict[str, Any]:
    if not manifest_path.is_file():
        raise RuntimeError("offline cache is incomplete: retrieval manifest is missing")
    manifest = _json(manifest_path, label="UC24-13 retrieval manifest")
    missing = [relative for relative in manifest.get("files", []) if not (root / relative).is_file()]
    if missing:
        raise RuntimeError(f"offline cache is incomplete: missing {', '.join(missing[:3])}")
    for resource in manifest.get("resources", []):
        archive = root / resource["archive_path"]
        if sha256(archive) != resource["archive_sha256"]:
            raise RuntimeError(f"offline cache archive hash mismatch: {resource['slug']}")
        inspect_tileset((root / resource["tileset_path"]).parent)
    return manifest


def fetch_uc24_13(
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

    source_manifest = _json(source_manifest_path, label="UC24-13 source manifest")
    package, package_headers = _request_json(source_manifest["package_api"])
    if package.get("success") is not True or not isinstance(package.get("result"), dict):
        raise RuntimeError("official CKAN package_show request was not successful")
    package_result = package["result"]
    resources_by_id = {item.get("id"): item for item in package_result.get("resources", [])}
    previous = _json(retrieval_manifest_path, label="UC24-13 retrieval manifest") if retrieval_manifest_path.is_file() else {}
    previous_by_id = {item["resource_id"]: item for item in previous.get("resources", [])}
    retrieved_at = datetime.now(tz=UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    archive_dir = cache_dir / "archives"
    assets_dir = cache_dir / "assets"
    archive_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    manifest_resources: list[dict[str, Any]] = []
    all_files: list[str] = []
    for selection in source_manifest.get("resources", []):
        resource_id = selection["resource_id"]
        try:
            official = resources_by_id[resource_id]
        except KeyError as error:
            raise RuntimeError(f"selected UC24-13 resource is missing from CKAN: {resource_id}") from error
        if not isinstance(official.get("url"), str):
            raise RuntimeError(f"selected UC24-13 resource has no download URL: {resource_id}")

        slug = selection["slug"]
        archive_path = archive_dir / f"{slug}.zip"
        asset_directory = assets_dir / slug
        prior = previous_by_id.get(resource_id, {})
        cached_inspection: dict[str, Any] | None = None
        if not force and archive_path.is_file() and asset_directory.is_dir():
            try:
                cached_inspection = inspect_tileset(asset_directory)
            except RuntimeError:
                cached_inspection = None
            expected_hash = prior.get("archive_sha256")
            if expected_hash and sha256(archive_path) != expected_hash:
                cached_inspection = None

        if cached_inspection is None:
            with tempfile.NamedTemporaryFile("wb", dir=cache_dir, delete=False) as handle:
                temporary_archive = Path(handle.name)
            try:
                download_headers = _download(official["url"], temporary_archive)
                if not zipfile.is_zipfile(temporary_archive):
                    raise RuntimeError(f"UC24-13 resource is not a ZIP archive: {slug}")
                with tempfile.TemporaryDirectory(dir=cache_dir) as temporary_directory:
                    staging = Path(temporary_directory)
                    extract_archive(temporary_archive, staging)
                    inspection = inspect_tileset(staging)
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
        manifest_resources.append(
            {
                "resource_id": resource_id,
                "slug": slug,
                "structure_class": selection["structure_class"],
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
                "archive_sha256": sha256(archive_path),
                "tileset_path": tileset_relative,
                "tileset_url": _asset_url(tileset_relative),
                **inspection,
            }
        )

    reference_resources: list[dict[str, Any]] = []
    for reference in source_manifest.get("reference_resources", []):
        row = {**reference, "status": "reference_only"}
        resource_id = reference.get("resource_id")
        if reference.get("package_id") == source_manifest["package_id"] and resource_id:
            try:
                official = resources_by_id[resource_id]
            except KeyError as error:
                raise RuntimeError(f"reference UC24-13 resource is missing from CKAN: {resource_id}") from error
            row.update(
                {
                    "name": official.get("name"),
                    "format": official.get("format"),
                    "download_url": official.get("url"),
                }
            )
        reference_resources.append(row)

    west = min(item["bounding_region"]["degrees_and_metres"][0] for item in manifest_resources)
    south = min(item["bounding_region"]["degrees_and_metres"][1] for item in manifest_resources)
    east = max(item["bounding_region"]["degrees_and_metres"][2] for item in manifest_resources)
    north = max(item["bounding_region"]["degrees_and_metres"][3] for item in manifest_resources)
    minimum_height = min(item["bounding_region"]["degrees_and_metres"][4] for item in manifest_resources)
    maximum_height = max(item["bounding_region"]["degrees_and_metres"][5] for item in manifest_resources)
    manifest = {
        "schema_version": 1,
        "dataset_id": source_manifest["dataset_id"],
        "scene_id": source_manifest["scene_id"],
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
        "extent_degrees_and_metres": [west, south, east, north, minimum_height, maximum_height],
        "feature_count": sum(item["feature_count"] for item in manifest_resources),
        "gml_id_count": sum(item["gml_id_count"] for item in manifest_resources),
        "resource_count": len(manifest_resources),
        "content_count": sum(item["content_count"] for item in manifest_resources),
        "files": sorted(set(all_files)),
        "resources": manifest_resources,
        "reference_resources": reference_resources,
        "identity_note": "Each rendered batch retains upstream gml_id and attributes in its B3DM batch table; resource ID, asset path and batch index keep identities source-specific.",
        "missing_value_semantics": "A missing or null source attribute remains unknown; no level, depth, accessibility or opening status is inferred.",
        "limitations": [
            "2024 demonstration data for selected Sapporo structures, not a complete or live station model",
            "not a routing graph and not evidence of legal public access or current opening status",
            "not suitable for engineering, evacuation or operational decisions without authoritative verification",
        ],
    }
    _atomic_json(retrieval_manifest_path, manifest)
    print(
        f"UC24-13 Sapporo cache ready: {len(manifest_resources)} resources, "
        f"{manifest['content_count']} B3DM contents, {manifest['feature_count']} batched features"
    )
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="refresh both selected archives from official URLs")
    parser.add_argument("--offline", action="store_true", help="validate only an existing complete local cache")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    fetch_uc24_13(force=args.force, offline=args.offline)


if __name__ == "__main__":
    main()
