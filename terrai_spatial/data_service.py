"""Read-only dataset service for the TerrAI exhibition API.

The committed JSON/GeoJSON files stay the canonical interchange and
provenance format; serving reads the spatially indexed store derived from
them by the ``store`` data task. This module is the only backend component
that knows where data lives; the browser consumes stable dataset keys and
API responses instead.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .store import (
    STORE_PATH,
    StoreSource,
    all_features,
    count_window,
    dataset_feature_count,
    dataset_kind,
    open_store,
    read_collection,
    read_document,
    read_envelope,
    verify_store,
    window_features,
)


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
    "uc24_13_sapporo": "data/plateau/uc24_13_sapporo/manifest.json",
    "osmSapporoUndergroundAccess": "data/osm/sapporo_underground_access/features.geojson",
    # osmBuildings retired (osm-basemap-tiles PR5): the Kanto OSM footprints are now
    # served as part of the merged self-hosted building PMTiles, not a windowed
    # store collection. The acquisition (osm_kanto) stays as a tile input.
    "kunijibanBoreholes": "data/external/kunijiban_borehole/manifest.json",
}
ALL_DATASETS = {**DATASETS, **FOUNDATION_DATASETS}
ASSET_MANIFEST_DATASETS = {
    "uc24_16_nihonbashi",
    "uc24_13_sapporo",
    "kunijibanBoreholes",
}
# Optional site-scene inputs remain queryable in the catalog but do not change
# the existing exhibition bootstrap's health denominator or visual chrome.
HEALTH_EXCLUDED_DATASETS = ASSET_MANIFEST_DATASETS | {"osmSapporoUndergroundAccess"}
SCENE_CATALOG_PATH = "data/scenes/underground/catalog.json"
SCENE_HANDOFFS = {
    "uc24_16_nihonbashi": "data/plateau/uc24_16_nihonbashi/scene_handoff.json",
    "uc24_13_sapporo": "data/plateau/uc24_13_sapporo/scene_handoff.json",
}

# The FL/SL/AL commitment is schema, not convention: every store row carries
# its tier and evidence state. Everything integrated today is observed —
# acquired evidence and deterministic transformations are FL, the heuristic
# screening products computed from them are AL, and no synthetic value exists
# yet. The first SL prediction set arrives under a model-run record, never as
# a relabelling. Per docs/architecture/FL_SL_AL_CONCEPT.md, the satellite
# embedding remains external FL even though a foundation model produced it.
DATASET_TIERS: dict[str, tuple[str, str]] = {
    "buildings": ("AL", "observed"),
    "buildingSummary": ("AL", "observed"),
    "roads": ("AL", "observed"),
    "roadSummary": ("AL", "observed"),
    "solar": ("AL", "observed"),
    "solarContext": ("FL", "observed"),
    "solarSummary": ("AL", "observed"),
    "hubs": ("AL", "observed"),
    "corridors": ("AL", "observed"),
    "delivery": ("AL", "observed"),
    "jointSummary": ("AL", "observed"),
    "gridScreen": ("FL", "observed"),
    "gsiEvacuation": ("FL", "observed"),
    "facilities": ("AL", "observed"),
    "embeddingEvidence": ("FL", "observed"),
    "embeddingSummary": ("FL", "observed"),
    "yokohamaZones": ("AL", "observed"),
    "mobaraZones": ("AL", "observed"),
    "multiscaleSummary": ("AL", "observed"),
    "landClassification50k": ("FL", "observed"),
    "floodHistory": ("FL", "observed"),
    "landHistory": ("FL", "observed"),
    "landslideWarning": ("FL", "observed"),
    "multistageFlood": ("FL", "observed"),
    "publishedLandPrice": ("FL", "observed"),
    "embankmentRegulation": ("FL", "observed"),
    "railway": ("FL", "observed"),
    "landUseMesh": ("FL", "observed"),
    "prefecturalLandPrice": ("FL", "observed"),
    "uc24_16_nihonbashi": ("FL", "observed"),
    "uc24_13_sapporo": ("FL", "observed"),
    "osmSapporoUndergroundAccess": ("FL", "observed"),
    "kunijibanBoreholes": ("FL", "observed"),
}


def store_sources() -> list[StoreSource]:
    """Every dataset the service exposes, as build sources for the store.

    GeoJSON datasets land in ``features``; JSON products, asset manifests and
    the scene catalog/handoffs land in ``documents`` under the keys the
    service uses today.
    """

    missing = sorted(set(ALL_DATASETS) - set(DATASET_TIERS))
    if missing:
        raise RuntimeError(f"datasets lack a tier assignment: {', '.join(missing)}")
    sources = []
    for key, relative in ALL_DATASETS.items():
        tier, evidence_state = DATASET_TIERS[key]
        kind = "features" if relative.endswith(".geojson") else "document"
        sources.append(StoreSource(key, relative, kind, tier, evidence_state))
    sources.append(StoreSource("sceneCatalog", SCENE_CATALOG_PATH, "document", "FL", "observed"))
    for owner, relative in SCENE_HANDOFFS.items():
        sources.append(StoreSource(f"sceneHandoff:{owner}", relative, "document", "FL", "observed"))
    return sources

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
    """Load, query and summarize the datasets through the derived store."""

    def __init__(self, root: Path = ROOT) -> None:
        self.root = root
        self._store: Any = None

    def _connection(self) -> Any:
        if self._store is None:
            path = self.root / STORE_PATH
            if not path.is_file():
                raise RuntimeError(
                    f"the spatial store is missing at {STORE_PATH}; "
                    "build it with: uv run python -m terrai_spatial data ensure"
                )
            self._store = open_store(path, check_same_thread=False)
        return self._store

    def require_store(self) -> None:
        """Refuse to serve from a missing or drifted store, loudly.

        Startup calls this so a broken pipeline surfaces as a named failure
        with the command that fixes it, never as quietly stale responses.
        """

        path = self.root / STORE_PATH
        if not path.is_file():
            raise RuntimeError(
                f"the spatial store is missing at {STORE_PATH}; "
                "build it with: uv run python -m terrai_spatial data ensure"
            )
        failures = verify_store(self.root, path, expected_keys=[source.key for source in store_sources()])
        if failures:
            raise RuntimeError(
                "the spatial store failed its manifest check: "
                + "; ".join(failures)
                + " — rebuild it with: uv run python -m terrai_spatial data ensure --only store"
            )

    def path_for(self, key: str) -> Path:
        try:
            relative = ALL_DATASETS[key]
        except KeyError as error:
            raise DatasetNotFoundError(key) from error
        return self.root / relative

    def _missing_from_store(self, key: str) -> RuntimeError:
        return RuntimeError(
            f"{key} is missing from the spatial store; "
            "rebuild it with: uv run python -m terrai_spatial data ensure --only store"
        )

    def _document(self, key: str) -> Any:
        value = read_document(self._connection(), key)
        if value is None:
            raise self._missing_from_store(key)
        return value

    def load(self, key: str) -> Any:
        if key not in ALL_DATASETS:
            raise DatasetNotFoundError(key)
        connection = self._connection()
        if dataset_kind(connection, key) == "document":
            return self._document(key)
        value = read_collection(connection, key)
        if value is None:
            raise self._missing_from_store(key)
        return value

    def scene_catalog(self) -> dict[str, Any]:
        """Return renderer-neutral scene discovery without adding a dataset key."""

        return self._document("sceneCatalog")

    def scene_handoff(self, owner_dataset_key: str) -> dict[str, Any]:
        """Resolve scene metadata through its existing Foundation dataset key."""

        if owner_dataset_key not in SCENE_HANDOFFS:
            raise DatasetNotFoundError(owner_dataset_key)
        return self._document(f"sceneHandoff:{owner_dataset_key}")

    def scene_bundle(self, scene_id: str) -> dict[str, Any]:
        """One catalogued scene with its full handoff, resolved by scene id.

        The scene id maps through the catalog to its `owner_dataset_key` — the
        only resolution path — so an unknown id fails here rather than growing
        a second lookup. The handoff passes through verbatim: `unresolved` and
        `not_applicable` evidence families, approved roots, timestamps,
        licences and audit indexes all stay exactly as published.
        """

        for entry in self.scene_catalog().get("scenes", []):
            if entry.get("scene_id") == scene_id:
                return {"scene": entry, "handoff": self.scene_handoff(entry["owner_dataset_key"])}
        raise DatasetNotFoundError(scene_id)

    @staticmethod
    def _read_json_file(path: Path) -> Any:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)

    def catalog(self) -> list[dict[str, Any]]:
        # The catalog describes the committed files themselves — existence,
        # modification time, readiness — so it reads them directly rather
        # than the store derived from them.
        rows = []
        for key, relative in ALL_DATASETS.items():
            path = self.root / relative
            exists = path.is_file()
            # Do not deserialize large on-demand layers merely to render health
            # or catalog metadata; that would defeat their delivery boundary.
            value = self._read_json_file(path) if exists and (key in DATASETS or key in ASSET_MANIFEST_DATASETS) else None
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
                    "scene_handoff_path": SCENE_HANDOFFS.get(key),
                    "scene_handoff_ready": (
                        self._safe_manifest_file_exists(SCENE_HANDOFFS[key])
                        if key in SCENE_HANDOFFS
                        else None
                    ),
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
        if root not in path.parents or not path.is_file() or path.stat().st_size == 0:
            return False
        if path.suffix not in {".json", ".geojson"}:
            return True
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return False
        return path.suffix != ".geojson" or value.get("type") == "FeatureCollection"

    def health(self) -> dict[str, Any]:
        catalog = [row for row in self.catalog() if row["key"] not in HEALTH_EXCLUDED_DATASETS]
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
        if key not in ALL_DATASETS:
            raise DatasetNotFoundError(key)
        connection = self._connection()
        envelope = read_envelope(connection, key)
        if envelope is None or envelope.get("type") != "FeatureCollection":
            raise ValueError(f"{key} is not a GeoJSON FeatureCollection")
        # Fast path — no attribute filter and no sort. The limit goes to SQL,
        # so a windowed or unwindowed query never materializes rows it would
        # discard, and `matched` comes from a count that reads no feature_json.
        # Without this an unbounded `limit`-only query on a million-row dataset
        # loaded and parsed every row before slicing (measured 45 s on
        # osmBuildings); it now returns in milliseconds.
        if not where and not sort:
            if bbox:
                matched = count_window(connection, key, bbox)
                rows = window_features(connection, key, bbox, limit=limit)
            else:
                matched = dataset_feature_count(connection, key)
                rows = all_features(connection, key, limit=limit)
            envelope["features"] = [json.loads(text) for _, text in rows]
            envelope["query"] = {"matched": matched, "returned": len(envelope["features"])}
            return envelope

        # Filtered/sorted path — the predicate and order both need every
        # matching feature in hand. Attribute filters stay in Python
        # deliberately: `equals` compares `str(value)` and Python treats
        # booleans as numbers, and no SQL expression reproduces either exactly
        # — the pinned-semantics tests are the record of that decision.
        rows = window_features(connection, key, bbox) if bbox else all_features(connection, key)
        features = [json.loads(text) for _, text in rows]
        if where:
            features = [
                feature
                for feature in features
                if self._matches(feature.get("properties", {}), where, equals, minimum, maximum)
            ]
        if sort:
            features = sorted(
                features,
                key=lambda feature: self._sortable(feature.get("properties", {}).get(sort)),
                reverse=descending,
            )
        envelope["features"] = features[:limit]
        envelope["query"] = {"matched": len(features), "returned": len(envelope["features"])}
        return envelope

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


service = DataService()
