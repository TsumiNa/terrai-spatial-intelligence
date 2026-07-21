"""Refresh the bounded OSM underground-access snapshot for the Sapporo scene."""

from __future__ import annotations

import argparse
import hashlib
import sys
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from terrai_spatial.pipeline.http import download_json  # noqa: E402
from terrai_spatial.pipeline.io import write_json_atomic  # noqa: E402
from terrai_spatial.pipeline.provenance import utc_timestamp  # noqa: E402
from terrai_spatial.pipeline.regions import SAPPORO_UNDERGROUND_ACCESS_BOUNDS  # noqa: E402

QUERY_PATH = Path("data/osm/sapporo_underground_access/query.overpassql")
OUTPUT_PATH = Path("data/osm/sapporo_underground_access/features.geojson")
METADATA_PATH = Path("data/osm/sapporo_underground_access/metadata.json")
OVERPASS_ENDPOINT = "https://maps.mail.ru/osm/tools/overpass/api/interpreter"
BBOX = list(SAPPORO_UNDERGROUND_ACCESS_BOUNDS)
WALKWAY_HIGHWAYS = {"footway", "pedestrian", "corridor", "steps"}


def _request_overpass(query: str) -> tuple[dict[str, Any], str]:
    payload = urlencode({"data": query}).encode("utf-8")
    value, provenance = download_json(
        OVERPASS_ENDPOINT,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=180,
    )
    if not isinstance(value, dict):
        raise RuntimeError("Overpass response root is not an object")
    return value, provenance["resolved_url"]


def _has_negative_number(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    for item in value.replace(",", ";").split(";"):
        try:
            if float(item.strip()) < 0:
                return True
        except ValueError:
            continue
    return False


def _only_non_negative_numeric_position(tags: dict[str, Any]) -> bool:
    values = [tags[name] for name in ("level", "layer") if isinstance(tags.get(name), str)]
    if not values:
        return False
    numbers: list[float] = []
    for value in values:
        for item in value.replace(",", ";").split(";"):
            try:
                numbers.append(float(item.strip()))
            except ValueError:
                return False
    return bool(numbers) and all(item >= 0 for item in numbers)


def _feature_class(tags: dict[str, Any]) -> str | None:
    if tags.get("railway") == "subway_entrance":
        return "subway_entrance"
    if tags.get("railway") == "station" and tags.get("station") == "subway":
        return "subway_station"
    if tags.get("public_transport") == "platform" and tags.get("subway") == "yes":
        return "subway_platform"
    if tags.get("railway") == "subway":
        return "subway_track"
    if tags.get("highway") in WALKWAY_HIGHWAYS:
        return "underground_walkway"
    return None


def _underground_evidence(tags: dict[str, Any]) -> list[str]:
    evidence: list[str] = []
    if tags.get("tunnel") not in {None, "no"}:
        evidence.append("tunnel")
    if tags.get("indoor") not in {None, "no"}:
        evidence.append("indoor")
    if "level" in tags:
        evidence.append("level_tag")
    if _has_negative_number(tags.get("level")):
        evidence.append("negative_level")
    if _has_negative_number(tags.get("layer")):
        evidence.append("negative_layer")
    return evidence


def _geometry(element: dict[str, Any]) -> dict[str, Any]:
    if element.get("type") == "node":
        lon = element.get("lon")
        lat = element.get("lat")
        if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
            raise RuntimeError(f"OSM node {element.get('id')} lacks coordinates")
        return {"type": "Point", "coordinates": [lon, lat]}
    if element.get("type") != "way":
        raise RuntimeError(f"unsupported OSM element type: {element.get('type')}")
    source_geometry = element.get("geometry")
    if not isinstance(source_geometry, list) or len(source_geometry) < 2:
        raise RuntimeError(f"OSM way {element.get('id')} lacks complete geometry")
    coordinates: list[list[float]] = []
    for point in source_geometry:
        if not isinstance(point, dict) or not isinstance(point.get("lon"), (int, float)) or not isinstance(
            point.get("lat"), (int, float)
        ):
            raise RuntimeError(f"OSM way {element.get('id')} has malformed geometry")
        coordinates.append([point["lon"], point["lat"]])
    if element.get("tags", {}).get("area") == "yes" and coordinates[0] == coordinates[-1]:
        return {"type": "Polygon", "coordinates": [coordinates]}
    return {"type": "LineString", "coordinates": coordinates}


def normalize_snapshot(
    document: dict[str, Any],
    *,
    query: str,
    retrieved_at: str,
    endpoint: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    elements = document.get("elements")
    if not isinstance(elements, list):
        raise RuntimeError("Overpass response has no elements array")
    seen: set[tuple[str, int]] = set()
    features: list[dict[str, Any]] = []
    omitted_restricted = 0
    omitted_non_underground = 0
    for element in elements:
        if not isinstance(element, dict):
            raise RuntimeError("Overpass element is not an object")
        element_type = element.get("type")
        element_id = element.get("id")
        version = element.get("version")
        timestamp = element.get("timestamp")
        tags = element.get("tags", {})
        if (
            element_type not in {"node", "way"}
            or not isinstance(element_id, int)
            or not isinstance(version, int)
            or not isinstance(timestamp, str)
            or not isinstance(tags, dict)
        ):
            raise RuntimeError("Overpass element lacks auditable identity metadata")
        identity = (element_type, element_id)
        if identity in seen:
            continue
        seen.add(identity)
        feature_class = _feature_class(tags)
        if feature_class is None:
            continue
        if feature_class == "underground_walkway" and tags.get("access") in {"no", "private"}:
            omitted_restricted += 1
            continue
        if (
            feature_class == "underground_walkway"
            and tags.get("tunnel") in {None, "no"}
            and not _has_negative_number(tags.get("level"))
            and not _has_negative_number(tags.get("layer"))
            and _only_non_negative_numeric_position(tags)
        ):
            omitted_non_underground += 1
            continue
        access = tags.get("access")
        if access in {"yes", "permissive", "designated"}:
            access_status = "tagged_public_or_permissive"
        elif access is None:
            access_status = "not_stated"
        else:
            access_status = f"tagged_{access}"
        features.append(
            {
                "type": "Feature",
                "id": f"osm/{element_type}/{element_id}",
                "geometry": _geometry(element),
                "properties": {
                    "scene_id": "sapporo-station-underground",
                    "evidence_source": "OpenStreetMap",
                    "evidence_status": "community_observation",
                    "feature_class": feature_class,
                    "osm_type": element_type,
                    "osm_id": element_id,
                    "osm_version": version,
                    "osm_changeset": element.get("changeset"),
                    "osm_timestamp": timestamp,
                    "source_url": f"https://www.openstreetmap.org/{element_type}/{element_id}",
                    "level": tags.get("level"),
                    "layer": tags.get("layer"),
                    "depth_m": None,
                    "elevation_m": None,
                    "public_access_status": access_status,
                    "underground_evidence": _underground_evidence(tags),
                    "tags": tags,
                },
            }
        )

    features.sort(key=lambda item: item["id"])
    feature_counts = dict(sorted(Counter(item["properties"]["feature_class"] for item in features).items()))
    query_sha256 = hashlib.sha256(query.encode("utf-8")).hexdigest()
    metadata = {
        "schema_version": 1,
        "dataset_id": "osm_sapporo_underground_access",
        "scene_id": "sapporo-station-underground",
        "retrieved_at": retrieved_at,
        "osm_base_timestamp": document.get("osm3s", {}).get("timestamp_osm_base"),
        "overpass_endpoint": endpoint,
        "overpass_generator": document.get("generator"),
        "query_path": QUERY_PATH.as_posix(),
        "query_sha256": query_sha256,
        "query_bbox": BBOX,
        "bbox_semantics": "The bbox selects intersecting OSM objects; complete source geometry is retained rather than clipped.",
        "crs": "EPSG:4326",
        "raw_element_count": len(elements),
        "feature_count": len(features),
        "feature_counts": feature_counts,
        "omitted_explicitly_restricted_walkways": omitted_restricted,
        "omitted_non_underground_walkways": omitted_non_underground,
        "license": "Open Database License (ODbL) 1.0",
        "attribution": "© OpenStreetMap contributors",
        "identity_note": "OSM type, ID, version, changeset and element timestamp are preserved independently from PLATEAU identities.",
        "missing_value_semantics": "Absent tags remain absent; unknown level, depth, accessibility and current opening status are not inferred.",
        "limitations": [
            "Community completeness, geometry accuracy and freshness are not guaranteed",
            "An absent access restriction is not proof of legal public access or current opening",
            "This snapshot is access context, not a routable or authoritative station graph",
        ],
    }
    collection = {
        "type": "FeatureCollection",
        "name": "osm_sapporo_underground_access",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
        "metadata": metadata,
        "features": features,
    }
    return collection, metadata


def fetch_osm_snapshot(*, root: Path = ROOT) -> tuple[dict[str, Any], dict[str, Any]]:
    query_path = root / QUERY_PATH
    query = query_path.read_text(encoding="utf-8")
    document, endpoint = _request_overpass(query)
    retrieved_at = utc_timestamp()
    collection, metadata = normalize_snapshot(
        document,
        query=query,
        retrieved_at=retrieved_at,
        endpoint=endpoint,
    )
    write_json_atomic(root / OUTPUT_PATH, collection)
    write_json_atomic(root / METADATA_PATH, metadata)
    print(
        f"OSM Sapporo underground snapshot ready: {metadata['feature_count']} features at "
        f"{metadata['osm_base_timestamp']}"
    )
    return collection, metadata


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(description=__doc__)


def main() -> None:
    build_parser().parse_args()
    fetch_osm_snapshot()


if __name__ == "__main__":
    main()
