#!/usr/bin/env python3
"""Build official-facility and multi-scale evidence products for the PoC."""

from __future__ import annotations

import csv
import io
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from terrai_spatial.pipeline.io import write_json_atomic  # noqa: E402
from terrai_spatial.pipeline.measurement import (  # noqa: E402
    distance_m,
    point_line_distance_m,
    project_line,
    project_point,
)
from terrai_spatial.pipeline.regions import STUDY_BOUNDS  # noqa: E402

DATA = ROOT / "data"

LOCAL_SOURCE_UPDATED_AT = "2026-04-01"
LOCAL_RETRIEVED_AT = "2026-07-20"


def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def read_csv_text(path: Path) -> str:
    """Read a source CSV as text, rewriting a Shift_JIS download as UTF-8 in place.

    Yokohama publishes its open-data CSVs in Shift_JIS, so a refreshed download
    is converted on first use and every later read is plain UTF-8.
    """
    raw = path.read_bytes()
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("cp932")
    path.write_text(text, encoding="utf-8", newline="")
    print(f"Converted {path.name} from Shift_JIS to UTF-8")
    return text


def data_as_of(*timestamps: str | None) -> str:
    """Latest provenance date among the inputs, as a plain date.

    This summary is committed to the repository, so its contents must not
    depend on when the build ran. A wall-clock value produces a diff on every
    rebuild, which hides real changes and makes `git status` useless for
    answering whether a rebuild changed anything.

    The audit question is "as of what data", not "when did the script run" —
    the latter is already in the Git history.
    """

    dates = sorted({value[:10] for value in timestamps if value})
    return dates[-1] if dates else ""


def feature_collection(features: list[dict]) -> dict:
    return {"type": "FeatureCollection", "features": features}


def centroid(feature: dict) -> list[float]:
    props = feature.get("properties", {})
    if "centroid" in props:
        return props["centroid"]
    geometry = feature["geometry"]
    if geometry["type"] == "Point":
        return geometry["coordinates"]
    if geometry["type"] == "Polygon":
        ring = geometry["coordinates"][0]
        return [sum(point[0] for point in ring) / len(ring), sum(point[1] for point in ring) / len(ring)]
    raise ValueError(f"Unsupported geometry: {geometry['type']}")


def clamp(value: float) -> float:
    return max(0.0, min(100.0, value))


def point_in_box(point: list[float], bounds: tuple[float, float, float, float]) -> bool:
    west, south, east, north = bounds
    return west <= point[0] <= east and south <= point[1] <= north


def facility_key(name: str | None) -> str:
    """Return a stable school/facility name key across national and local labels."""
    normalized = unicodedata.normalize("NFKC", name or "").strip()
    normalized = re.split(r"\s+", normalized, maxsplit=1)[0]
    return normalized.removeprefix("横浜市立")


def yokohama_ward(address: str | None) -> str | None:
    """Extract a Yokohama ward from an official address without assuming study bounds."""
    normalized = unicodedata.normalize("NFKC", address or "")
    match = re.search(r"横浜市([^区]+区)", normalized)
    return match.group(1) if match else None


def local_facility_rows(source: Path) -> list[dict[str, str]]:
    with io.StringIO(read_csv_text(source), newline="") as handle:
        return [
            row
            for row in csv.DictReader(handle)
            if row["Ward"] == "保土ケ谷区"
            and row["Type"] == "地域防災拠点"
            and point_in_box([float(row["Lon"]), float(row["Lat"])], STUDY_BOUNDS["yokohama"])
        ]


def reconcile_facility_sources(gsi_features: list[dict], local_rows: list[dict[str, str]]) -> list[dict]:
    """Use GSI shelters as the base and Yokohama rows as validation/supplements."""
    emergency_by_key: dict[str, dict] = {}
    for feature in gsi_features:
        props = feature["properties"]
        if props["designation_type"] != "designated_emergency_evacuation_place":
            continue
        key = facility_key(props.get("name"))
        evidence = emergency_by_key.setdefault(
            key,
            {
                "hazards": set(),
                "common_ids": [],
                "source_updated_at": props.get("source_updated_at"),
                "retrieved_at": props.get("retrieved_at"),
            },
        )
        evidence["hazards"].update(props.get("hazards", []))
        if props.get("common_id"):
            evidence["common_ids"].append(props["common_id"])

    local_by_key = {facility_key(row["Name"]): row for row in local_rows}
    matched_local_keys: set[str] = set()
    reconciled = []
    for feature in gsi_features:
        props = feature["properties"]
        point = feature["geometry"]["coordinates"]
        if props["designation_type"] != "designated_shelter" or not point_in_box(point, STUDY_BOUNDS["yokohama"]):
            continue
        key = facility_key(props.get("name"))
        local = local_by_key.get(key)
        if local:
            matched_local_keys.add(key)
        emergency = emergency_by_key.get(
            key,
            {"hazards": set(), "common_ids": [], "source_updated_at": None, "retrieved_at": None},
        )
        reconciled.append(
            {
                "geometry": feature["geometry"],
                "properties": {
                    "name": props["name"],
                    "type": "指定避難所",
                    "definition": local["Definition"] if local else "災害対策基本法に基づく指定避難所",
                    "address": props["address"],
                    "ward": local["Ward"] if local else yokohama_ward(props.get("address")),
                    "base_source_id": "gsi_designated_evacuation",
                    "base_source_scope": "national",
                    "source_reconciliation": "national_base_local_validated" if local else "national_base_only",
                    "gsi_common_id": props.get("common_id"),
                    "gsi_emergency_place_common_ids": emergency["common_ids"],
                    "gsi_designated_hazards": sorted(emergency["hazards"]),
                    "gsi_emergency_source_updated_at": emergency["source_updated_at"],
                    "gsi_emergency_retrieved_at": emergency["retrieved_at"],
                    "national_source_updated_at": props.get("source_updated_at"),
                    "national_retrieved_at": props.get("retrieved_at"),
                    "local_source_id": "yokohama_official_disaster_bases" if local else None,
                    "local_name": local["Name"] if local else None,
                    "local_type": local["Type"] if local else None,
                    "local_source_updated_at": LOCAL_SOURCE_UPDATED_AT if local else None,
                    "local_retrieved_at": LOCAL_RETRIEVED_AT if local else None,
                },
            }
        )

    for key, local in local_by_key.items():
        if key in matched_local_keys:
            continue
        emergency = emergency_by_key.get(
            key,
            {"hazards": set(), "common_ids": [], "source_updated_at": None, "retrieved_at": None},
        )
        reconciled.append(
            {
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(local["Lon"]), float(local["Lat"])],
                },
                "properties": {
                    "name": local["Name"],
                    "type": local["Type"],
                    "definition": local["Definition"],
                    "address": local["Address"],
                    "ward": local["Ward"],
                    "base_source_id": "yokohama_official_disaster_bases",
                    "base_source_scope": "local_supplement",
                    "source_reconciliation": "local_supplement_not_in_national_shelter_base",
                    "gsi_common_id": None,
                    "gsi_emergency_place_common_ids": emergency["common_ids"],
                    "gsi_designated_hazards": sorted(emergency["hazards"]),
                    "gsi_emergency_source_updated_at": emergency["source_updated_at"],
                    "gsi_emergency_retrieved_at": emergency["retrieved_at"],
                    "national_source_updated_at": None,
                    "national_retrieved_at": None,
                    "local_source_id": "yokohama_official_disaster_bases",
                    "local_name": local["Name"],
                    "local_type": local["Type"],
                    "local_source_updated_at": LOCAL_SOURCE_UPDATED_AT,
                    "local_retrieved_at": LOCAL_RETRIEVED_AT,
                },
            }
        )
    return reconciled


def official_facilities(buildings: list[dict], roads: list[dict]) -> list[dict]:
    building_points = [(item, project_point(centroid(item))) for item in buildings]
    high_points = [point for item, point in building_points if item["properties"]["risk_band"] == "high"]
    road_lines = [(item, project_line(item["geometry"]["coordinates"])) for item in roads]
    local_source = DATA / "external" / "yokohama" / "hinanjo_20260401.csv"
    gsi_source = load(DATA / "external" / "gsi_evacuation" / "yokohama_evacuation.geojson")
    source_records = reconcile_facility_sources(gsi_source["features"], local_facility_rows(local_source))
    results = []
    for record in source_records:
        point = project_point(record["geometry"]["coordinates"])
        nearest_building, building_point = min(building_points, key=lambda pair: distance_m(point, pair[1]))
        building_distance = distance_m(point, building_point)
        building_props = nearest_building["properties"]
        nearest_road, road_line = min(road_lines, key=lambda pair: point_line_distance_m(point, pair[1]))
        road_distance = point_line_distance_m(point, road_line)
        served_high = sum(distance_m(point, high_point) <= 250 for high_point in high_points)
        roof_area = building_props.get("footprint_m2", 0) if building_distance <= 90 else 0
        pv_proxy = round(roof_area * 0.12, 1)
        site_safety = clamp(100 - building_props.get("risk_score", 50))
        access = clamp(0.65 * nearest_road["properties"]["priority_score"] + 0.35 * (100 - road_distance / 1.5))
        demand = clamp(served_high / 30 * 100)
        energy = clamp(pv_proxy / 70 * 100)
        score = round(0.30 * site_safety + 0.25 * access + 0.30 * demand + 0.15 * energy)
        results.append(
            {
                "type": "Feature",
                "id": f"official-shelter-{len(results) + 1}",
                "geometry": record["geometry"],
                "properties": {
                    **record["properties"],
                    "official_status": "observed_official",
                    "resilience_score": score,
                    "served_high_risk_buildings": served_high,
                    "nearest_road_m": round(road_distance),
                    "nearest_road_name": nearest_road["properties"].get("name") or "未命名道路",
                    "nearest_road_priority": nearest_road["properties"]["priority_score"],
                    "matched_roof_m": round(building_distance),
                    "matched_roof_area_m2": round(roof_area, 1),
                    "pv_kwp_proxy": pv_proxy,
                    "site_safety_component": round(site_safety),
                    "access_component": round(access),
                    "community_need_component": round(demand),
                    "energy_component": round(energy),
                    "decision": "官方设施；优先核查屋顶结构、储能、备用电源与灾时道路连续性",
                    "limitations": "建筑轮廓为最近邻匹配；容量和结构未经现场验证",
                },
            }
        )
    return sorted(results, key=lambda item: item["properties"]["resilience_score"], reverse=True)


def mean_embedding_change(features: list[dict]) -> float | None:
    if not features:
        return None
    return round(sum(item["properties"]["change_score"] for item in features) / len(features), 1)


def build_zones(
    region: str,
    columns: int,
    rows: int,
    buildings: list[dict],
    roads: list[dict],
    solar: list[dict],
    facilities: list[dict],
    embeddings: list[dict],
) -> list[dict]:
    west, south, east, north = STUDY_BOUNDS[region]
    dx, dy = (east - west) / columns, (north - south) / rows
    zones = []
    for row in range(rows):
        for column in range(columns):
            bounds = (west + column * dx, south + row * dy, west + (column + 1) * dx, south + (row + 1) * dy)
            zone_buildings = [item for item in buildings if point_in_box(centroid(item), bounds)] if region == "yokohama" else []
            zone_roads = [item for item in roads if any(point_in_box(point, bounds) for point in item["geometry"]["coordinates"])] if region == "yokohama" else []
            zone_solar = [item for item in solar if point_in_box(centroid(item), bounds)] if region == "mobara" else []
            zone_facilities = [item for item in facilities if point_in_box(centroid(item), bounds)] if region == "yokohama" else []
            zone_embeddings = [item for item in embeddings if item["properties"]["region"] == region and point_in_box(centroid(item), bounds)]

            if region == "yokohama":
                building_count = len(zone_buildings)
                high_count = sum(item["properties"]["risk_band"] == "high" for item in zone_buildings)
                high_share = high_count / max(building_count, 1)
                road_priority = max((item["properties"]["priority_score"] for item in zone_roads), default=0)
                facility_gap = 0 if zone_facilities else 100
                action_score = round(0.45 * clamp(high_share * 300) + 0.35 * road_priority + 0.20 * facility_gap)
                properties = {
                    "building_count": building_count,
                    "high_risk_buildings": high_count,
                    "high_risk_share_pct": round(high_share * 100, 1),
                    "max_road_priority": road_priority,
                    "official_facilities": len(zone_facilities),
                    "action_score": action_score,
                    "action": "设施服务缺口" if not zone_facilities and high_count >= 5 else "道路与建筑联合复核",
                }
            else:
                preferred = sum(item["properties"]["status"] == "preferred" for item in zone_solar)
                mean_score = round(sum(item["properties"]["score"] for item in zone_solar) / max(len(zone_solar), 1), 1)
                action_score = round(0.65 * mean_score + 0.35 * clamp(preferred / max(len(zone_solar), 1) * 100)) if zone_solar else 0
                properties = {
                    "solar_cells": len(zone_solar),
                    "preferred_cells": preferred,
                    "mean_solar_score": mean_score,
                    "action_score": action_score,
                    "action": "优先土地与并网尽调" if action_score >= 70 else "保留观察",
                }

            zone_id = f"{region.upper()}-{row + 1}{column + 1}"
            properties.update(
                {
                    "region": region,
                    "zone_id": zone_id,
                    "embedding_change_score": mean_embedding_change(zone_embeddings),
                    "embedding_support_cells": len(zone_embeddings),
                    "embedding_used_in_score": False,
                    "context_density": "dense" if (len(zone_buildings) >= 80 or len(zone_solar) >= 4) else "moderate" if (len(zone_buildings) >= 25 or len(zone_solar) >= 2) else "sparse",
                    "evidence_scales": ["10m raster", "object", "100–300m neighborhood", "regional gate"],
                }
            )
            zones.append(
                {
                    "type": "Feature",
                    "id": zone_id,
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[bounds[0], bounds[1]], [bounds[2], bounds[1]], [bounds[2], bounds[3]], [bounds[0], bounds[3]], [bounds[0], bounds[1]]]],
                    },
                    "properties": properties,
                }
            )
    return sorted(zones, key=lambda item: item["properties"]["action_score"], reverse=True)


def main() -> None:
    buildings = load(DATA / "yokohama" / "building_risk.geojson")["features"]
    roads = load(DATA / "yokohama" / "road_priority.geojson")["features"]
    solar = load(DATA / "mobara" / "site_cells.geojson")["features"]
    embeddings = load(DATA / "google" / "satellite_embedding" / "embedding_evidence.geojson")["features"]
    gsi_metadata = load(DATA / "external" / "gsi_evacuation" / "metadata.json")
    facilities = official_facilities(buildings, roads)
    yoko_zones = build_zones("yokohama", 4, 4, buildings, roads, solar, facilities, embeddings)
    mobara_zones = build_zones("mobara", 5, 4, buildings, roads, solar, facilities, embeddings)

    write_json_atomic(DATA / "yokohama" / "official_facility_resilience.geojson", feature_collection(facilities))
    write_json_atomic(DATA / "evidence" / "yokohama_zones.geojson", feature_collection(yoko_zones))
    write_json_atomic(DATA / "evidence" / "mobara_zones.geojson", feature_collection(mobara_zones))
    write_json_atomic(
        DATA / "evidence" / "multiscale_summary.json",
        {
            "data_as_of": data_as_of(
                gsi_metadata["source_updated_at"],
                gsi_metadata["retrieved_at"],
                LOCAL_SOURCE_UPDATED_AT,
                LOCAL_RETRIEVED_AT,
            ),
            "official_facilities": {
                "source_rows_in_study_area": len(facilities),
                "national_base_source": "GSI designated shelters, municipality 14100",
                "national_source_updated_at": gsi_metadata["source_updated_at"],
                "national_retrieved_at": gsi_metadata["retrieved_at"],
                "local_validation_source": "Yokohama City regional disaster prevention bases",
                "local_source_updated_at": LOCAL_SOURCE_UPDATED_AT,
                "local_retrieved_at": LOCAL_RETRIEVED_AT,
                "reconciliation_counts": {
                    status: sum(
                        item["properties"]["source_reconciliation"] == status for item in facilities
                    )
                    for status in (
                        "national_base_local_validated",
                        "national_base_only",
                        "local_supplement_not_in_national_shelter_base",
                    )
                },
                "source_policy": "National coverage is the base; local data validates and adds explicitly labelled records.",
                "license": "GSI content terms / PDL 1.0 and Yokohama City CC BY 4.0",
                "important_note": "Official location is observed; roof match, PV capacity and resilience score are PoC proxies.",
            },
            "satellite_embedding": {
                "status": "integrated_observed",
                "resolution_m": 10,
                "years": [2023, 2024],
                "used_in_score": False,
                "role": ["annual change evidence", "similarity features", "future sparse-label transfer"],
            },
            "sparse_context_evidence": {
                "source": "TsumiNa/geo_pfn docs/sparse-context-results.html",
                "task": "Haneda Su prediction from whole-borehole context",
                "query_boreholes": 48,
                "context_boreholes": [3, 6, 12, 25, 50, 100, 192],
                "mid_sparse_regime": [25, 50],
                "geopfn_rmse_l": [28.50, 24.65, 20.74, 20.03, 20.01, 18.92, 19.12],
                "tabicl_rmse_l": [24.74, 24.77, 21.09, 26.33, 24.01, 20.61, 19.24],
                "hgbt_rmse_l": [29.05, 22.74, 21.97, 21.47, 20.81, 19.67, 18.53],
                "guardrail": "Mechanism evidence only; not transferred as an accuracy claim for surface-risk modules.",
            },
            "scale_contract": [
                {"scale": "5–10 m", "inputs": "GSI DEM / Satellite Embedding", "role": "terrain and surface-change evidence"},
                {"scale": "object", "inputs": "buildings / roads / official facilities / solar cells", "role": "actionable assets"},
                {"scale": "100–300 m", "inputs": "neighborhood context", "role": "demand, access and service gap"},
                {"scale": "region / portfolio", "inputs": "grid gate / evidence coverage / project queue", "role": "investment sequencing"},
            ],
        },
    )
    print(f"Built {len(facilities)} official facilities, {len(yoko_zones)} Yokohama zones and {len(mobara_zones)} Mobara zones")


if __name__ == "__main__":
    main()
