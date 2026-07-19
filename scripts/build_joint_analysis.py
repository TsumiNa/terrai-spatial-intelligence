#!/usr/bin/env python3
"""Build TerrAI cross-module decision products from the three PoC datasets.

The script intentionally uses only Python's standard library so that the demo can
be regenerated without a GIS stack. All distances are local planar approximations
and should be replaced by a projected CRS workflow in a production system.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
LAT0 = math.radians(35.4465)
M_PER_DEG_LAT = 111_320.0
M_PER_DEG_LON = M_PER_DEG_LAT * math.cos(LAT0)


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def xy(point: list[float]) -> tuple[float, float]:
    return point[0] * M_PER_DEG_LON, point[1] * M_PER_DEG_LAT


def distance_m(a: list[float], b: list[float]) -> float:
    ax, ay = xy(a)
    bx, by = xy(b)
    return math.hypot(ax - bx, ay - by)


def point_segment_distance_m(point: list[float], a: list[float], b: list[float]) -> float:
    px, py = xy(point)
    ax, ay = xy(a)
    bx, by = xy(b)
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def point_line_distance_m(point: list[float], coordinates: list[list[float]]) -> float:
    return min(
        point_segment_distance_m(point, coordinates[index], coordinates[index + 1])
        for index in range(len(coordinates) - 1)
    )


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def feature_collection(features: list[dict]) -> dict:
    return {"type": "FeatureCollection", "features": features}


def build_compound_corridors(buildings: list[dict], roads: list[dict]) -> list[dict]:
    building_points = [(feature, feature["properties"]["centroid"]) for feature in buildings]
    results = []
    for road in roads:
        line = road["geometry"]["coordinates"]
        nearby = [
            feature
            for feature, point in building_points
            if point_line_distance_m(point, line) <= 55
        ]
        high = [feature for feature in nearby if feature["properties"]["risk_band"] == "high"]
        if not high:
            continue
        average_risk = sum(feature["properties"]["risk_score"] for feature in nearby) / len(nearby)
        road_score = road["properties"]["priority_score"]
        demand_score = clamp(len(high) / 8 * 100)
        compound_score = round(0.45 * road_score + 0.35 * demand_score + 0.20 * average_risk)
        if compound_score < 62:
            continue
        properties = dict(road["properties"])
        properties.update(
            {
                "compound_score": compound_score,
                "joint_band": "priority" if compound_score >= 75 else "watch",
                "joint_nearby_buildings": len(nearby),
                "joint_high_risk_buildings": len(high),
                "joint_average_building_risk": round(average_risk, 1),
                "joint_action": "边坡排水、道路通行与邻近建筑联合巡检",
            }
        )
        results.append({"type": "Feature", "id": road.get("id"), "geometry": road["geometry"], "properties": properties})
    return sorted(results, key=lambda feature: feature["properties"]["compound_score"], reverse=True)


def build_resilience_hubs(buildings: list[dict], roads: list[dict]) -> list[dict]:
    high_points = [
        feature["properties"]["centroid"]
        for feature in buildings
        if feature["properties"]["risk_band"] == "high"
    ]
    results = []
    for building in buildings:
        props = building["properties"]
        footprint = props.get("footprint_m2") or 0
        if footprint < 140 or props["risk_band"] == "high" or props["slope_deg"] > 12:
            continue

        point = props["centroid"]
        nearest_road = min(
            roads,
            key=lambda road: point_line_distance_m(point, road["geometry"]["coordinates"]),
        )
        nearest_distance = point_line_distance_m(point, nearest_road["geometry"]["coordinates"])
        if nearest_distance > 150:
            continue
        served_high = sum(distance_m(point, high_point) <= 150 for high_point in high_points)
        if served_high < 2:
            continue

        pv_kwp = round(footprint * 0.12, 1)
        pv_score = clamp(pv_kwp / 45 * 100)
        proximity_score = clamp(100 - nearest_distance / 1.5)
        road_score = nearest_road["properties"]["priority_score"]
        access_score = 0.65 * road_score + 0.35 * proximity_score
        community_need_score = clamp(served_high / 18 * 100)
        safety_score = clamp(100 - props["risk_score"])
        hub_score = round(0.30 * pv_score + 0.25 * access_score + 0.35 * community_need_score + 0.10 * safety_score)
        if hub_score < 45:
            continue

        result_props = dict(props)
        result_props.update(
            {
                "hub_score": hub_score,
                "hub_band": "priority" if hub_score >= 65 else "candidate",
                "pv_kwp_proxy": pv_kwp,
                "served_high_risk_buildings": served_high,
                "nearest_road_m": round(nearest_distance),
                "nearest_road_name": nearest_road["properties"].get("name") or "未命名道路",
                "nearest_road_priority": road_score,
                "pv_component": round(pv_score),
                "access_component": round(access_score),
                "community_need_component": round(community_need_score),
                "site_safety_component": round(safety_score),
                "joint_action": "屋顶光伏＋储能＋社区应急服务节点候选",
                "assumption": "可用屋顶面积60%，组件功率密度0.20 kWp/m²",
            }
        )
        results.append({"type": "Feature", "id": building.get("id"), "geometry": building["geometry"], "properties": result_props})
    return sorted(results, key=lambda feature: feature["properties"]["hub_score"], reverse=True)[:30]


def build_solar_delivery_cells(cells: list[dict]) -> list[dict]:
    results = []
    for cell in cells:
        props = cell["properties"]
        if props["status"] == "reject":
            continue
        delivery_score = round(
            0.45 * props["score"]
            + 0.20 * props["slope_component"]
            + 0.20 * props["access_component"]
            + 0.15 * props["grid_component"]
        )
        if delivery_score < 68:
            continue
        result_props = dict(props)
        result_props.update(
            {
                "delivery_score": delivery_score,
                "delivery_band": "priority" if delivery_score >= 82 else "candidate",
                "joint_action": "优先开展并网、道路运输与地形工程联合踏勘",
            }
        )
        results.append({"type": "Feature", "id": cell.get("id"), "geometry": cell["geometry"], "properties": result_props})
    return sorted(results, key=lambda feature: feature["properties"]["delivery_score"], reverse=True)


def main() -> None:
    buildings = load_json(DATA / "yokohama" / "building_risk.geojson")["features"]
    roads = load_json(DATA / "yokohama" / "road_priority.geojson")["features"]
    cells = load_json(DATA / "mobara" / "site_cells.geojson")["features"]

    corridors = build_compound_corridors(buildings, roads)
    hubs = build_resilience_hubs(buildings, roads)
    delivery_cells = build_solar_delivery_cells(cells)

    write_json(DATA / "joint" / "compound_corridors.geojson", feature_collection(corridors))
    write_json(DATA / "joint" / "resilience_hubs.geojson", feature_collection(hubs))
    write_json(DATA / "joint" / "solar_delivery_cells.geojson", feature_collection(delivery_cells))
    write_json(
        DATA / "joint" / "joint_summary.json",
        {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "method": "PoC heuristic spatial multi-criteria analysis",
            "resilience_hubs": {
                "count": len(hubs),
                "priority_count": sum(feature["properties"]["hub_band"] == "priority" for feature in hubs),
                "pv_capacity_proxy_kwp": round(sum(feature["properties"]["pv_kwp_proxy"] for feature in hubs)),
                "served_high_risk_building_links": sum(feature["properties"]["served_high_risk_buildings"] for feature in hubs),
            },
            "compound_corridors": {
                "count": len(corridors),
                "priority_count": sum(feature["properties"]["joint_band"] == "priority" for feature in corridors),
                "road_length_km": round(sum(feature["properties"]["length_m"] for feature in corridors) / 1000, 1),
                "high_risk_building_links": sum(feature["properties"]["joint_high_risk_buildings"] for feature in corridors),
            },
            "solar_delivery_cells": {
                "count": len(delivery_cells),
                "priority_count": sum(feature["properties"]["delivery_band"] == "priority" for feature in delivery_cells),
                "area_ha": round(sum(feature["properties"]["area_ha"] for feature in delivery_cells), 1),
            },
            "important_note": "Counts describe screening relationships, not unique beneficiaries or engineering feasibility.",
        },
    )

    print(f"Built {len(hubs)} hubs, {len(corridors)} corridors, {len(delivery_cells)} delivery-ready solar cells")


if __name__ == "__main__":
    main()
