"""Read-only JSON/GeoJSON service for the TerrAI exhibition API.

The PoC intentionally keeps the foundation layer as independent files.  This
module is the only backend component that knows their filesystem locations;
the browser consumes stable dataset keys and API responses instead.
"""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

DATASETS: dict[str, str] = {
    "buildings": "data/yokohama/building_risk.geojson",
    "buildingSummary": "data/yokohama/building_summary.json",
    "roads": "data/yokohama/road_priority.geojson",
    "roadSummary": "data/yokohama/road_summary.json",
    "solar": "data/mobara/site_cells.geojson",
    "solarContext": "data/mobara/context.geojson",
    "solarSummary": "data/mobara/solar_summary.json",
    "hubs": "data/joint/resilience_hubs.geojson",
    "corridors": "data/joint/compound_corridors.geojson",
    "delivery": "data/joint/solar_delivery_cells.geojson",
    "jointSummary": "data/joint/joint_summary.json",
    "gridScreen": "data/mobara/tepco_grid_screen.json",
    "gsiEvacuation": "data/external/gsi_evacuation/yokohama_evacuation.geojson",
    "facilities": "data/yokohama/official_facility_resilience.geojson",
    "embeddingEvidence": "data/google/satellite_embedding/embedding_evidence.geojson",
    "embeddingSummary": "data/google/satellite_embedding/summary.json",
    "yokohamaZones": "data/evidence/yokohama_zones.geojson",
    "mobaraZones": "data/evidence/mobara_zones.geojson",
    "multiscaleSummary": "data/evidence/multiscale_summary.json",
}

# Large FL layers are queryable but deliberately excluded from the exhibition
# bootstrap. Clients request only the spatial window needed by an analysis.
FOUNDATION_DATASETS: dict[str, str] = {
    "landClassification50k": "data/mlit/land_classification_50k.geojson",
    "floodHistory": "data/mlit/flood_history.geojson",
    "landHistory": "data/mlit/land_history.geojson",
    "landslideWarning": "data/mlit/landslide_warning.geojson",
    "multistageFlood": "data/mlit/multistage_flood.geojson",
    "publishedLandPrice": "data/mlit/published_land_price.geojson",
    "embankmentRegulation": "data/mlit/embankment_regulation.geojson",
    "railway": "data/mlit/railway.geojson",
    "landUseMesh": "data/mlit/land_use_mesh.geojson",
    "prefecturalLandPrice": "data/mlit/prefectural_land_price.geojson",
    "uc24_16_nihonbashi": "data/plateau/uc24_16_nihonbashi/manifest.json",
}
ALL_DATASETS = {**DATASETS, **FOUNDATION_DATASETS}
ASSET_MANIFEST_DATASETS = {"uc24_16_nihonbashi"}

SOURCE_GROUPS = (
    {"name": "GSI", "role": "terrain, designated evacuation and visual basemaps", "access": "public"},
    {"name": "MLIT", "role": "land, hazard, transport and price foundation layers", "access": "public; dataset-specific terms"},
    {"name": "OpenStreetMap", "role": "buildings, roads and context", "access": "public"},
    {"name": "Yokohama Open Data", "role": "official disaster facilities", "access": "public"},
    {"name": "NASA POWER", "role": "solar climate baseline", "access": "public"},
    {"name": "TEPCO public system data", "role": "regional grid screen", "access": "restricted redistribution"},
    {"name": "Google Satellite Embedding", "role": "annual change and similarity evidence", "access": "CC BY 4.0"},
)


class DatasetNotFoundError(KeyError):
    """Raised when an unknown public dataset key is requested."""


class DataService:
    """Load, cache, query and summarize the file-backed PoC datasets."""

    def __init__(self, root: Path = ROOT) -> None:
        self.root = root
        self._cache: dict[str, tuple[int, Any]] = {}

    def path_for(self, key: str) -> Path:
        try:
            relative = ALL_DATASETS[key]
        except KeyError as error:
            raise DatasetNotFoundError(key) from error
        return self.root / relative

    def load(self, key: str) -> Any:
        path = self.path_for(key)
        modified_ns = path.stat().st_mtime_ns
        cached = self._cache.get(key)
        if cached and cached[0] == modified_ns:
            return deepcopy(cached[1])
        with path.open(encoding="utf-8") as handle:
            value = json.load(handle)
        self._cache[key] = (modified_ns, value)
        return deepcopy(value)

    def catalog(self) -> list[dict[str, Any]]:
        rows = []
        for key, relative in ALL_DATASETS.items():
            path = self.root / relative
            exists = path.is_file()
            # Do not deserialize large on-demand layers merely to render health
            # or catalog metadata; that would defeat their delivery boundary.
            value = self.load(key) if exists and (key in DATASETS or key in ASSET_MANIFEST_DATASETS) else None
            asset_roots = None
            if key in ASSET_MANIFEST_DATASETS:
                manifest_files = value.get("files", []) if isinstance(value, dict) else []
                ready = exists and bool(manifest_files) and all(
                    self._safe_manifest_file_exists(item) for item in manifest_files
                )
                asset_roots = [
                    resource["tileset_url"]
                    for resource in value.get("resources", [])
                    if isinstance(resource, dict) and isinstance(resource.get("tileset_url"), str)
                ] if isinstance(value, dict) else []
            else:
                ready = exists
            rows.append(
                {
                    "key": key,
                    "path": relative,
                    "ready": ready,
                    "kind": (
                        "asset_manifest"
                        if key in ASSET_MANIFEST_DATASETS
                        else "geojson" if relative.endswith(".geojson") else "json"
                    ),
                    "delivery": "bootstrap" if key in DATASETS else "on_demand",
                    "feature_count": (
                        value.get("feature_count")
                        if key in ASSET_MANIFEST_DATASETS and isinstance(value, dict)
                        else len(value.get("features", [])) if isinstance(value, dict) else None
                    ),
                    "asset_roots": asset_roots,
                    "modified_at": (
                        datetime.fromtimestamp(path.stat().st_mtime, tz=UTC).isoformat() if exists else None
                    ),
                }
            )
        return rows

    def _safe_manifest_file_exists(self, relative: Any) -> bool:
        if not isinstance(relative, str):
            return False
        path = (self.root / relative).resolve()
        root = self.root.resolve()
        return root in path.parents and path.is_file() and path.stat().st_size > 0

    def health(self) -> dict[str, Any]:
        catalog = [row for row in self.catalog() if row["key"] not in ASSET_MANIFEST_DATASETS]
        ready = sum(1 for row in catalog if row["ready"])
        return {
            "status": "ready" if ready == len(catalog) else "degraded",
            "datasets_ready": ready,
            "datasets_total": len(catalog),
            "source_groups": len(SOURCE_GROUPS),
            "traceability": "all displayed values expose source or calculation audit",
            "checked_at": datetime.now(tz=UTC).isoformat(),
        }

    def bootstrap(self) -> dict[str, Any]:
        payload = {key: self.load(key) for key in DATASETS}
        facilities = payload["facilities"].get("features", [])
        payload["facilitySummary"] = {
            "count": len(facilities),
            "pv_kwp_proxy": round(sum(item["properties"].get("pv_kwp_proxy", 0) for item in facilities)),
            "served_high_risk_buildings": sum(
                item["properties"].get("served_high_risk_buildings", 0) for item in facilities
            ),
            "mean_resilience_score": (
                round(sum(item["properties"].get("resilience_score", 0) for item in facilities) / len(facilities))
                if facilities
                else 0
            ),
        }
        payload["recommendations"] = self.recommendations()
        payload["meta"] = {
            **self.health(),
            "source_catalog": list(SOURCE_GROUPS),
            "data_model": "file-backed JSON/GeoJSON",
            "api_version": "v1",
        }
        return payload

    def recommendations(self) -> dict[str, dict[str, Any]]:
        return {
            "slope": self._select("buildings", "risk_score", lambda props: props.get("risk_band") == "high"),
            "roads": self._select("roads", "priority_score", lambda props: props.get("priority_score", 0) >= 70),
            "solar": self._select("solar", "score", lambda props: props.get("status") == "preferred"),
            "facilities": self._select("facilities", "resilience_score"),
            "hubs": self._select("hubs", "hub_score"),
            "corridors": self._select("corridors", "compound_score"),
            "delivery": self._select("delivery", "delivery_score"),
            "constraints": self._select(
                "solar",
                "slope_deg",
                lambda props: props.get("status") == "reject",
                secondary=lambda props: len(props.get("reject_reasons", [])),
            ),
            "embedding": self._select("embeddingEvidence", "change_score"),
            "embeddingYokohama": self._select(
                "embeddingEvidence", "change_score", lambda props: props.get("region") == "yokohama"
            ),
            "embeddingMobara": self._select(
                "embeddingEvidence", "change_score", lambda props: props.get("region") == "mobara"
            ),
        }

    def recommendation(self, analysis: str) -> dict[str, Any]:
        try:
            return self.recommendations()[analysis]
        except KeyError as error:
            raise DatasetNotFoundError(analysis) from error

    def query_features(
        self,
        key: str,
        *,
        where: str | None = None,
        equals: str | None = None,
        minimum: float | None = None,
        maximum: float | None = None,
        sort: str | None = None,
        descending: bool = True,
        limit: int = 5000,
        bbox: tuple[float, float, float, float] | None = None,
    ) -> dict[str, Any]:
        value = self.load(key)
        if not isinstance(value, dict) or value.get("type") != "FeatureCollection":
            raise ValueError(f"{key} is not a GeoJSON FeatureCollection")
        features = value.get("features", [])
        if where:
            features = [
                feature
                for feature in features
                if self._matches(feature.get("properties", {}), where, equals, minimum, maximum)
            ]
        if bbox:
            features = [feature for feature in features if self._intersects_bbox(feature.get("geometry"), bbox)]
        if sort:
            features = sorted(
                features,
                key=lambda feature: self._sortable(feature.get("properties", {}).get(sort)),
                reverse=descending,
            )
        result = deepcopy(value)
        result["features"] = features[:limit]
        result["query"] = {"matched": len(features), "returned": len(result["features"])}
        return result

    def _select(
        self,
        key: str,
        score_field: str,
        predicate: Any = None,
        secondary: Any = None,
    ) -> dict[str, Any]:
        collection = self.load(key)
        features = collection.get("features", [])
        if predicate:
            features = [feature for feature in features if predicate(feature.get("properties", {}))]
        features = sorted(
            features,
            key=lambda feature: (
                secondary(feature.get("properties", {})) if secondary else 0,
                self._sortable(feature.get("properties", {}).get(score_field)),
            ),
            reverse=True,
        )
        return {"type": "FeatureCollection", "features": features}

    @staticmethod
    def _sortable(value: Any) -> tuple[int, Any]:
        return (0, "") if value is None else (1, value)

    @staticmethod
    def _matches(
        properties: dict[str, Any],
        field: str,
        equals: str | None,
        minimum: float | None,
        maximum: float | None,
    ) -> bool:
        value = properties.get(field)
        if equals is not None and str(value) != equals:
            return False
        if minimum is not None and (not isinstance(value, (int, float)) or value < minimum):
            return False
        if maximum is not None and (not isinstance(value, (int, float)) or value > maximum):
            return False
        return True

    @classmethod
    def _intersects_bbox(
        cls, geometry: dict[str, Any] | None, bbox: tuple[float, float, float, float]
    ) -> bool:
        if not geometry:
            return False
        coordinates = list(cls._coordinate_pairs(geometry.get("coordinates")))
        if not coordinates:
            return False
        min_x, min_y, max_x, max_y = bbox
        geometry_min_x = min(x for x, _ in coordinates)
        geometry_max_x = max(x for x, _ in coordinates)
        geometry_min_y = min(y for _, y in coordinates)
        geometry_max_y = max(y for _, y in coordinates)
        return not (
            geometry_max_x < min_x
            or geometry_min_x > max_x
            or geometry_max_y < min_y
            or geometry_min_y > max_y
        )

    @classmethod
    def _coordinate_pairs(cls, value: Any):
        if isinstance(value, list) and len(value) >= 2 and all(isinstance(item, (int, float)) for item in value[:2]):
            yield float(value[0]), float(value[1])
            return
        if isinstance(value, list):
            for item in value:
                yield from cls._coordinate_pairs(item)


service = DataService()
