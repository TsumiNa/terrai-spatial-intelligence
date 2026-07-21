"""Build renderer-neutral handoffs for the canonical underground scenes."""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path, PurePosixPath
from typing import Any

from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from terrai_spatial.pipeline.io import read_json_object, write_json_atomic  # noqa: E402

CATALOG_PATH = Path("data/scenes/underground/catalog.json")
HANDOFF_PATHS = {
    "nihonbashi-utilities": Path("data/plateau/uc24_16_nihonbashi/scene_handoff.json"),
    "sapporo-station-underground": Path("data/plateau/uc24_13_sapporo/scene_handoff.json"),
}
EVIDENCE_FAMILIES = (
    "terrain_buildings_context",
    "utility_networks",
    "underground_structures",
    "access_topology",
    "boreholes",
    "strata",
    "predicted_fields",
)
UNAVAILABLE_KEYS = {"availability", "reason"}
GEOGRAPHIC_TO_ECEF = Transformer.from_crs("EPSG:4979", "EPSG:4978", always_xy=True)
ECEF_TO_GEOGRAPHIC = Transformer.from_crs("EPSG:4978", "EPSG:4979", always_xy=True)


def _read_json(root: Path, relative: str) -> dict[str, Any]:
    return read_json_object(root / relative, label=f"scene input {relative}")


def _apply_matrix(matrix: list[float], point: tuple[float, float, float]) -> tuple[float, float, float]:
    x, y, z = point
    return (
        matrix[0] * x + matrix[1] * y + matrix[2] * z + matrix[3],
        matrix[4] * x + matrix[5] * y + matrix[6] * z + matrix[7],
        matrix[8] * x + matrix[9] * y + matrix[10] * z + matrix[11],
    )


def local_frame(extent: list[float], *, height_reference: str, vertical_datum: str) -> dict[str, Any]:
    if (
        len(extent) != 6
        or not all(isinstance(item, (int, float)) and math.isfinite(item) for item in extent)
        or extent[0] >= extent[2]
        or extent[1] >= extent[3]
        or extent[4] > extent[5]
    ):
        raise RuntimeError("scene extent must contain ordered west, south, east, north, minimum and maximum")

    longitude = (extent[0] + extent[2]) / 2
    latitude = (extent[1] + extent[3]) / 2
    height = (extent[4] + extent[5]) / 2
    world_origin = GEOGRAPHIC_TO_ECEF.transform(longitude, latitude, height)
    lon = math.radians(longitude)
    lat = math.radians(latitude)
    east = (-math.sin(lon), math.cos(lon), 0.0)
    north = (-math.sin(lat) * math.cos(lon), -math.sin(lat) * math.sin(lon), math.cos(lat))
    up = (math.cos(lat) * math.cos(lon), math.cos(lat) * math.sin(lon), math.sin(lat))

    def translated_row(axis: tuple[float, float, float]) -> list[float]:
        return [*axis, -sum(axis[index] * world_origin[index] for index in range(3))]

    world_to_local = [
        *translated_row(east),
        *translated_row(north),
        *translated_row(up),
        0.0,
        0.0,
        0.0,
        1.0,
    ]
    local_to_world = [
        east[0],
        north[0],
        up[0],
        world_origin[0],
        east[1],
        north[1],
        up[1],
        world_origin[1],
        east[2],
        north[2],
        up[2],
        world_origin[2],
        0.0,
        0.0,
        0.0,
        1.0,
    ]
    return {
        "source_crs": "EPSG:4979",
        "source_axis_order": ["longitude_degrees", "latitude_degrees", "ellipsoid_height_metres"],
        "world_crs": "EPSG:4978",
        "world_axis_order": ["ecef_x_metres", "ecef_y_metres", "ecef_z_metres"],
        "local_axis_convention": {"x": "east", "y": "north", "z": "up"},
        "local_unit": "metre",
        "geographic_extent_degrees_and_metres": extent,
        "origin_geographic_degrees_and_metres": [longitude, latitude, height],
        "origin_world_ecef_metres": list(world_origin),
        "world_to_local_matrix_row_major": world_to_local,
        "local_to_world_matrix_row_major": local_to_world,
        "height_reference": height_reference,
        "vertical_datum": vertical_datum,
        "orthometric_vertical_datum": "unknown",
        "round_trip_tolerance": {"longitude_latitude_degrees": 1e-8, "height_metres": 1e-4},
    }


def world_to_local(frame: dict[str, Any], longitude: float, latitude: float, height: float) -> tuple[float, float, float]:
    world = GEOGRAPHIC_TO_ECEF.transform(longitude, latitude, height)
    return _apply_matrix(frame["world_to_local_matrix_row_major"], world)


def local_to_world(frame: dict[str, Any], point: tuple[float, float, float]) -> tuple[float, float, float]:
    ecef = _apply_matrix(frame["local_to_world_matrix_row_major"], point)
    return ECEF_TO_GEOGRAPHIC.transform(*ecef)


def _available_source(
    manifest: dict[str, Any],
    resources: list[dict[str, Any]],
    *,
    audit_index_path: str,
) -> dict[str, Any]:
    return {
        "dataset_id": manifest["dataset_id"],
        "resource_ids": sorted(resource["resource_id"] for resource in resources),
        "retrieved_at": manifest["retrieved_at"],
        "source_updated_at": manifest["package_metadata_modified"],
        "license": {"name": manifest["license"], "url": manifest["license_url"]},
        "audit_index_path": audit_index_path,
        "asset_paths": sorted(resource["tileset_path"] for resource in resources),
        "feature_count": sum(resource["feature_count"] for resource in resources),
    }


def _available(source: dict[str, Any]) -> dict[str, Any]:
    return {"availability": "available", "evidence_class": "observed", "sources": [source]}


def _unavailable(availability: str, reason: str) -> dict[str, str]:
    if availability not in {"unresolved", "not_applicable"}:
        raise RuntimeError(f"invalid evidence availability: {availability}")
    return {"availability": availability, "reason": reason}


def _path_is_approved(relative: str, approved_roots: list[str]) -> bool:
    path = PurePosixPath(relative)
    if path.is_absolute() or ".." in path.parts:
        return False
    return any(path == PurePosixPath(root) or PurePosixPath(root) in path.parents for root in approved_roots)


def validate_handoff(handoff: dict[str, Any]) -> None:
    if set(handoff.get("evidence_families", {})) != set(EVIDENCE_FAMILIES):
        raise RuntimeError(f"{handoff.get('scene_id')} does not declare the complete evidence-family contract")
    approved_roots = handoff.get("approved_roots")
    if not isinstance(approved_roots, list) or not approved_roots:
        raise RuntimeError(f"{handoff.get('scene_id')} has no approved roots")

    for family, evidence in handoff["evidence_families"].items():
        availability = evidence.get("availability")
        if availability == "available":
            if evidence.get("evidence_class") != "observed" or not evidence.get("sources"):
                raise RuntimeError(f"available {family} evidence must identify observed sources")
            for source in evidence["sources"]:
                required = {
                    "dataset_id",
                    "resource_ids",
                    "retrieved_at",
                    "source_updated_at",
                    "license",
                    "audit_index_path",
                    "asset_paths",
                    "feature_count",
                }
                if not required.issubset(source) or not source["resource_ids"] or not source["asset_paths"]:
                    raise RuntimeError(f"available {family} evidence has incomplete provenance")
                if not isinstance(source["feature_count"], int) or source["feature_count"] <= 0:
                    raise RuntimeError(f"available {family} evidence has no positive feature count")
                paths = [source["audit_index_path"], *source["asset_paths"]]
                if not all(isinstance(path, str) and _path_is_approved(path, approved_roots) for path in paths):
                    raise RuntimeError(f"available {family} evidence escapes its approved scene roots")
        elif availability in {"unresolved", "not_applicable"}:
            if set(evidence) != UNAVAILABLE_KEYS:
                raise RuntimeError(f"unavailable {family} evidence carries fabricated metadata")
        else:
            raise RuntimeError(f"invalid {family} evidence availability: {availability}")

    frame = handoff["local_frame"]
    extent = frame["geographic_extent_degrees_and_metres"]
    samples = (
        (extent[0], extent[1], extent[4]),
        frame["origin_geographic_degrees_and_metres"],
        (extent[2], extent[3], extent[5]),
    )
    tolerance = frame["round_trip_tolerance"]
    for longitude, latitude, height in samples:
        recovered = local_to_world(frame, world_to_local(frame, longitude, latitude, height))
        if (
            abs(recovered[0] - longitude) > tolerance["longitude_latitude_degrees"]
            or abs(recovered[1] - latitude) > tolerance["longitude_latitude_degrees"]
            or abs(recovered[2] - height) > tolerance["height_metres"]
        ):
            raise RuntimeError(f"{handoff['scene_id']} coordinate round trip exceeds its tolerance")


def _osm_source(metadata: dict[str, Any], feature_count: int) -> dict[str, Any]:
    return {
        "dataset_id": metadata["dataset_id"],
        "resource_ids": [metadata["query_sha256"]],
        "retrieved_at": metadata["retrieved_at"],
        "source_updated_at": metadata["osm_base_timestamp"],
        "license": {
            "name": metadata["license"],
            "url": "https://opendatacommons.org/licenses/odbl/1-0/",
        },
        "audit_index_path": "data/osm/sapporo_underground_access/features.geojson",
        "asset_paths": ["data/osm/sapporo_underground_access/features.geojson"],
        "feature_count": feature_count,
    }


def build_scene_handoffs(root: Path = ROOT) -> dict[str, Any]:
    utilities = _read_json(root, "data/plateau/uc24_16_nihonbashi/manifest.json")
    structures = _read_json(root, "data/plateau/uc24_13_sapporo/manifest.json")
    osm = _read_json(root, "data/osm/sapporo_underground_access/metadata.json")
    osm_features = _read_json(root, "data/osm/sapporo_underground_access/features.geojson")
    features = osm_features.get("features")
    if osm_features.get("type") != "FeatureCollection" or not isinstance(features, list):
        raise RuntimeError("OSM access snapshot must be a GeoJSON FeatureCollection")
    if osm.get("feature_count") != len(features):
        raise RuntimeError(
            f"OSM feature_count metadata is {osm.get('feature_count')}; snapshot contains {len(features)}"
        )
    if (
        utilities.get("scene_id") != "nihonbashi-utilities"
        or structures.get("scene_id") != "sapporo-station-underground"
        or osm.get("scene_id") != "sapporo-station-underground"
    ):
        raise RuntimeError("source scene IDs do not preserve Nihonbashi/Sapporo isolation")

    utility_extent = utilities["extent_degrees_and_metres"]
    structure_extent = structures["extent_degrees_and_metres"]
    if not (
        utility_extent[2] < structure_extent[0]
        or structure_extent[2] < utility_extent[0]
        or utility_extent[3] < structure_extent[1]
        or structure_extent[3] < utility_extent[1]
    ):
        raise RuntimeError("canonical scene extents unexpectedly overlap")
    osm_bbox = osm["query_bbox"]
    if not (
        structure_extent[0] - 1e-9 <= osm_bbox[0] <= osm_bbox[2] <= structure_extent[2] + 1e-9
        and structure_extent[1] - 1e-9 <= osm_bbox[1] <= osm_bbox[3] <= structure_extent[3] + 1e-9
    ):
        raise RuntimeError("OSM access context is outside the Sapporo structure extent")

    network_resources = sorted(
        [item for item in utilities["resources"] if item["utility_class"].endswith(("_pipe", "_cable"))],
        key=lambda item: item["resource_id"],
    )
    access_resources = sorted(
        [item for item in utilities["resources"] if item["utility_class"].endswith(("_manhole", "_handhole"))],
        key=lambda item: item["resource_id"],
    )
    if not network_resources or not access_resources:
        raise RuntimeError("UC24-16 must retain both network and access-structure resources")

    nihonbashi = {
        "schema_version": "1.0",
        "scene_id": "nihonbashi-utilities",
        "purpose": "Observed underground utility and access-structure scene",
        "owner_dataset_key": "uc24_16_nihonbashi",
        "foundation_layer_only": True,
        "approved_roots": [
            "data/external/plateau_uc24_16",
            "data/plateau/uc24_16_nihonbashi",
        ],
        "local_frame": local_frame(
            utility_extent,
            height_reference=utilities["height_reference"],
            vertical_datum=utilities["vertical_datum"],
        ),
        "evidence_families": {
            "terrain_buildings_context": _unavailable(
                "unresolved", "No co-located terrain or above-ground building context is integrated"
            ),
            "utility_networks": _available(
                _available_source(
                    utilities,
                    network_resources,
                    audit_index_path="data/plateau/uc24_16_nihonbashi/audit_index.json",
                )
            ),
            "underground_structures": _unavailable(
                "not_applicable", "Public underground-space structures are outside this utility scene"
            ),
            "access_topology": _available(
                _available_source(
                    utilities,
                    access_resources,
                    audit_index_path="data/plateau/uc24_16_nihonbashi/audit_index.json",
                )
            ),
            "boreholes": _unavailable("unresolved", "No qualified borehole observations are integrated"),
            "strata": _unavailable("unresolved", "No qualified strata observations are integrated"),
            "predicted_fields": _unavailable("unresolved", "No qualified SL prediction is integrated"),
        },
    }

    sapporo = {
        "schema_version": "1.0",
        "scene_id": "sapporo-station-underground",
        "purpose": "Observed underground public-space scene with independent OSM access context",
        "owner_dataset_key": "uc24_13_sapporo",
        "foundation_layer_only": True,
        "approved_roots": [
            "data/external/plateau_uc24_13",
            "data/plateau/uc24_13_sapporo",
            "data/osm/sapporo_underground_access",
        ],
        "local_frame": local_frame(
            structure_extent,
            height_reference=structures["height_reference"],
            vertical_datum=structures["vertical_datum"],
        ),
        "evidence_families": {
            "terrain_buildings_context": _unavailable(
                "unresolved", "No co-located terrain or above-ground building context is integrated"
            ),
            "utility_networks": _unavailable(
                "not_applicable", "The Nihonbashi utility sample must not be merged into Sapporo"
            ),
            "underground_structures": _available(
                _available_source(
                    structures,
                    sorted(structures["resources"], key=lambda item: item["resource_id"]),
                    audit_index_path="data/plateau/uc24_13_sapporo/manifest.json",
                )
            ),
            "access_topology": _available(_osm_source(osm, len(features))),
            "boreholes": _unavailable("unresolved", "No qualified borehole observations are integrated"),
            "strata": _unavailable("unresolved", "No qualified strata observations are integrated"),
            "predicted_fields": _unavailable("unresolved", "No qualified SL prediction is integrated"),
        },
    }

    handoffs = [nihonbashi, sapporo]
    for handoff in handoffs:
        validate_handoff(handoff)
        write_json_atomic(root / HANDOFF_PATHS[handoff["scene_id"]], handoff)

    catalog = {
        "schema_version": "1.0",
        "coordinate_contract": "EPSG:4979 geographic -> EPSG:4978 ECEF -> scene-local ENU metres",
        "scenes": [
            {
                "scene_id": item["scene_id"],
                "purpose": item["purpose"],
                "owner_dataset_key": item["owner_dataset_key"],
                "handoff_path": HANDOFF_PATHS[item["scene_id"]].as_posix(),
                "geographic_extent_degrees_and_metres": item["local_frame"][
                    "geographic_extent_degrees_and_metres"
                ],
                "origin_geographic_degrees_and_metres": item["local_frame"][
                    "origin_geographic_degrees_and_metres"
                ],
                "evidence_availability": {
                    family: evidence["availability"]
                    for family, evidence in item["evidence_families"].items()
                },
            }
            for item in handoffs
        ],
    }
    write_json_atomic(root / CATALOG_PATH, catalog)
    return catalog


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    catalog = build_scene_handoffs()
    print(f"Built {len(catalog['scenes'])} underground scene handoffs")


if __name__ == "__main__":
    main()
