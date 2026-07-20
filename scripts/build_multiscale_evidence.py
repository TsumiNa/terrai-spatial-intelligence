#!/usr/bin/env python3
"""Build official-facility and multi-scale evidence products for the PoC."""

from __future__ import annotations

import csv
import io
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
LAT0 = math.radians(35.446)
M_PER_DEG_LAT = 111_320.0
M_PER_DEG_LON = M_PER_DEG_LAT * math.cos(LAT0)

BOUNDS = {
    "yokohama": (139.5835, 35.4426, 139.5935, 35.4504),
    "mobara": (140.2757, 35.4387, 140.2913, 35.4513),
}


def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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


def feature_collection(features: list[dict]) -> dict:
    return {"type": "FeatureCollection", "features": features}


def xy(point: tuple[float, float] | list[float]) -> tuple[float, float]:
    return point[0] * M_PER_DEG_LON, point[1] * M_PER_DEG_LAT


def distance(a: tuple[float, float] | list[float], b: tuple[float, float] | list[float]) -> float:
    ax, ay = xy(a)
    bx, by = xy(b)
    return math.hypot(ax - bx, ay - by)


def point_segment_distance(point: list[float], a: list[float], b: list[float]) -> float:
    px, py = xy(point)
    ax, ay = xy(a)
    bx, by = xy(b)
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def point_line_distance(point: list[float], coordinates: list[list[float]]) -> float:
    return min(point_segment_distance(point, coordinates[index], coordinates[index + 1]) for index in range(len(coordinates) - 1))


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


def official_facilities(buildings: list[dict], roads: list[dict]) -> list[dict]:
    high_points = [centroid(item) for item in buildings if item["properties"]["risk_band"] == "high"]
    source = DATA / "external" / "yokohama" / "hinanjo_20260401.csv"
    results = []
    with io.StringIO(read_csv_text(source), newline="") as handle:
        for row in csv.DictReader(handle):
            if row["Ward"] != "保土ケ谷区" or row["Type"] != "地域防災拠点":
                continue
            point = [float(row["Lon"]), float(row["Lat"])]
            if not point_in_box(point, BOUNDS["yokohama"]):
                continue

            nearest_building = min(buildings, key=lambda item: distance(point, centroid(item)))
            building_distance = distance(point, centroid(nearest_building))
            building_props = nearest_building["properties"]
            nearest_road = min(roads, key=lambda item: point_line_distance(point, item["geometry"]["coordinates"]))
            road_distance = point_line_distance(point, nearest_road["geometry"]["coordinates"])
            served_high = sum(distance(point, high_point) <= 250 for high_point in high_points)
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
                    "geometry": {"type": "Point", "coordinates": point},
                    "properties": {
                        "name": row["Name"],
                        "type": row["Type"],
                        "definition": row["Definition"],
                        "address": row["Address"],
                        "ward": row["Ward"],
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
    west, south, east, north = BOUNDS[region]
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
    facilities = official_facilities(buildings, roads)
    yoko_zones = build_zones("yokohama", 4, 4, buildings, roads, solar, facilities, embeddings)
    mobara_zones = build_zones("mobara", 5, 4, buildings, roads, solar, facilities, embeddings)

    write(DATA / "yokohama" / "official_facility_resilience.geojson", feature_collection(facilities))
    write(DATA / "evidence" / "yokohama_zones.geojson", feature_collection(yoko_zones))
    write(DATA / "evidence" / "mobara_zones.geojson", feature_collection(mobara_zones))
    write(
        DATA / "evidence" / "multiscale_summary.json",
        {
            "generated_at": "2026-07-20",
            "official_facilities": {
                "source_rows_in_study_area": len(facilities),
                "source": "Yokohama City regional disaster prevention bases, updated 2026-04-01",
                "license": "CC BY 4.0",
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
