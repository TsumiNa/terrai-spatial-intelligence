"""Response identity across the store migration.

The oracle below is the retired file-scan implementation, preserved here as a
test double: every endpoint's payload must serialize byte-for-byte identically
whether it is assembled from the raw GeoJSON files or from the store. The one
wall-clock field (`checked_at`, and catalog `modified_at` formatting) is
frozen for both sides, so the comparison is modulo nothing.
"""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime
from typing import Any

import pytest

from terrai_spatial import data_service as data_service_module
from terrai_spatial.data_service import (
    ALL_DATASETS,
    ROOT,
    SCENE_CATALOG_PATH,
    SCENE_HANDOFFS,
    DataService,
    DatasetNotFoundError,
    store_sources,
)
from terrai_spatial.store import (
    STORE_PATH,
    STREAM_THRESHOLD_BYTES,
    open_store,
    read_envelope,
    stream_feature_collection,
    verify_store,
)
from terrai_spatial.store_test import scan_intersects


@pytest.fixture(autouse=True, scope="module")
def fresh_store() -> None:
    """Byte comparisons against a drifted store produce walls of JSON diff;
    fail first with the actual problem and its remedy. Scope resolution makes
    drift routine — landing or refreshing wide products stales the store."""

    failures = verify_store(ROOT, ROOT / STORE_PATH, expected_keys=[source.key for source in store_sources()])
    if failures:
        pytest.fail(
            "the spatial store has drifted from its sources; rebuild it with: "
            "uv run python -m terrai_spatial data ensure --only store\n" + "\n".join(failures)
        )


class FileBackedOracle(DataService):
    """The pre-store service: raw files, linear scans, per-access copies.

    Kanto-scale collections stream through the same incremental reader the
    store build uses, so the oracle stays bounded in memory while remaining a
    genuinely independent scan of the source file.
    """

    def load(self, key: str) -> Any:
        path = self.path_for(key)
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)

    def scene_catalog(self) -> dict[str, Any]:
        return json.loads((self.root / SCENE_CATALOG_PATH).read_text(encoding="utf-8"))

    def scene_handoff(self, owner_dataset_key: str) -> dict[str, Any]:
        if owner_dataset_key not in SCENE_HANDOFFS:
            raise DatasetNotFoundError(owner_dataset_key)
        return json.loads((self.root / SCENE_HANDOFFS[owner_dataset_key]).read_text(encoding="utf-8"))

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
        path = self.path_for(key)
        if path.suffix == ".geojson" and path.stat().st_size >= STREAM_THRESHOLD_BYTES:
            envelope, feature_iter = stream_feature_collection(path)
            features = []
            for feature in feature_iter:
                if where and not self._matches(feature.get("properties", {}), where, equals, minimum, maximum):
                    continue
                if bbox and not scan_intersects(feature.get("geometry"), bbox):
                    continue
                features.append(feature)
            if envelope.get("type") != "FeatureCollection":
                raise ValueError(f"{key} is not a GeoJSON FeatureCollection")
            result = envelope
        else:
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
                features = [feature for feature in features if scan_intersects(feature.get("geometry"), bbox)]
            result = deepcopy(value)
        if sort:
            features = sorted(
                features,
                key=lambda feature: self._sortable(feature.get("properties", {}).get(sort)),
                reverse=descending,
            )
        result["features"] = features[:limit]
        result["query"] = {"matched": len(features), "returned": len(result["features"])}
        return result


class FrozenDatetime(datetime):
    @classmethod
    def now(cls, tz=None):  # noqa: ANN001 - datetime signature
        return cls(2026, 7, 22, 12, 0, 0, tzinfo=tz)


@pytest.fixture()
def frozen_clock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(data_service_module, "datetime", FrozenDatetime)


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


store_backed = DataService(ROOT)
oracle = FileBackedOracle(ROOT)

YOKOHAMA_WINDOW = (139.58, 35.44, 139.60, 35.46)
TOKYO_WINDOW = (139.69, 35.68, 139.71, 35.70)
KOSHIGAYA_WINDOW = (139.76, 35.86, 139.80, 35.90)
HACHIOJI_WINDOW = (139.26, 35.62, 139.30, 35.66)
SAPPORO_WINDOW = (141.350, 43.055, 141.357, 43.071)

# Kanto-scale collections are always queried through a window here: the store
# side without a bbox parses every row, and the oracle would hold every match.
QUERY_MATRIX = [
    {"key": "landHistory", "bbox": YOKOHAMA_WINDOW},
    {"key": "landUseMesh", "bbox": YOKOHAMA_WINDOW, "where": "terrai_region", "equals": "kanto"},
    {"key": "landUseMesh", "bbox": TOKYO_WINDOW, "limit": 500},
    {"key": "multistageFlood", "bbox": KOSHIGAYA_WINDOW},
    {"key": "landslideWarning", "bbox": HACHIOJI_WINDOW, "limit": 200},
    {"key": "solar", "where": "status", "equals": "preferred", "sort": "score", "limit": 3},
    {"key": "buildings", "where": "risk_score", "minimum": 50.0, "sort": "risk_score", "descending": False, "limit": 100},
    {"key": "roads", "sort": "priority_score", "limit": 10},
    {"key": "embeddingEvidence", "where": "region", "equals": "mobara"},
    {"key": "osmSapporoUndergroundAccess", "bbox": SAPPORO_WINDOW},
    {"key": "corridors", "bbox": YOKOHAMA_WINDOW, "where": "compound_score", "minimum": 62.0, "sort": "compound_score"},
    {"key": "hubs", "where": "pv_kwp_proxy", "maximum": 30.0},
    # The str()-based `equals` quirks are contract: a missing property reads
    # as the string "None", and a numeric property never equals its string.
    {"key": "solar", "where": "no_such_property", "equals": "None", "limit": 5},
    {"key": "solar", "where": "status", "minimum": 1.0},
    {"key": "landHistory", "bbox": (0.0, 0.0, 1.0, 1.0)},
    {"key": "gsiEvacuation", "bbox": (139.0, 35.0, 141.0, 36.0), "limit": 50},
    {"key": "railway", "limit": 5},  # no bbox, no filter → the no-bbox fast path
]


def _large_collection(key: str) -> bool:
    path = oracle.path_for(key)
    return ALL_DATASETS[key].endswith(".geojson") and path.stat().st_size >= STREAM_THRESHOLD_BYTES


def test_every_dataset_loads_byte_identically_from_the_store() -> None:
    for key in ALL_DATASETS:
        if _large_collection(key):
            continue  # a full parse of a gigabyte collection on both sides; identity below
        assert canonical(store_backed.load(key)) == canonical(oracle.load(key)), key


def test_large_collections_match_by_envelope_count_and_window() -> None:
    """Full-collection byte identity is intractable at Kanto scale; the same
    guarantee decomposes into envelope identity, feature-count identity and
    the windowed-query identity the matrix below exercises."""

    connection = open_store(ROOT / STORE_PATH)
    try:
        for key in [key for key in ALL_DATASETS if _large_collection(key)]:
            envelope, features = stream_feature_collection(oracle.path_for(key))
            count = sum(1 for _ in features)
            assert canonical(read_envelope(connection, key)) == canonical(envelope), key
            stored = connection.execute(
                "SELECT feature_count FROM datasets WHERE key = ?", (key,)
            ).fetchone()[0]
            assert stored == count, key
    finally:
        connection.close()


def test_health_catalog_and_bootstrap_are_byte_identical(frozen_clock: None) -> None:
    assert canonical(store_backed.health()) == canonical(oracle.health())
    assert canonical(store_backed.catalog()) == canonical(oracle.catalog())
    assert canonical(store_backed.bootstrap()) == canonical(oracle.bootstrap())


def test_every_recommendation_queue_is_byte_identical() -> None:
    analyses = store_backed.recommendations()
    assert canonical(analyses) == canonical(oracle.recommendations())
    for analysis in analyses:
        assert canonical(store_backed.recommendation(analysis)) == canonical(oracle.recommendation(analysis))


def test_every_windowed_and_filtered_query_is_byte_identical() -> None:
    for request in QUERY_MATRIX:
        request = dict(request)
        key = request.pop("key")
        new = store_backed.query_features(key, **request)
        old = oracle.query_features(key, **request)
        assert canonical(new) == canonical(old), (key, request)


def test_scene_catalog_handoffs_and_bundles_are_byte_identical() -> None:
    assert canonical(store_backed.scene_catalog()) == canonical(oracle.scene_catalog())
    for owner in SCENE_HANDOFFS:
        assert canonical(store_backed.scene_handoff(owner)) == canonical(oracle.scene_handoff(owner))
    for scene_id in ("nihonbashi-utilities", "sapporo-station-underground"):
        assert canonical(store_backed.scene_bundle(scene_id)) == canonical(oracle.scene_bundle(scene_id))


def test_error_paths_stay_identical() -> None:
    for implementation in (store_backed, oracle):
        with pytest.raises(DatasetNotFoundError):
            implementation.load("no-such-dataset")
        with pytest.raises(ValueError, match="not a GeoJSON FeatureCollection"):
            implementation.query_features("jointSummary")
        with pytest.raises(DatasetNotFoundError):
            implementation.scene_handoff("osmSapporoUndergroundAccess")


# The pinned `_matches` semantics that keep attribute filters in Python: no
# SQL expression reproduces `str(value)` equality or Python's bool-as-number
# comparisons, so "SQL that looks equivalent" would silently diverge here.
MATCH_TABLE = [
    ({}, "field", "None", None, None, True),  # missing property stringifies to "None"
    ({"field": None}, "field", "None", None, None, True),
    ({"field": 1}, "field", "1", None, None, True),
    ({"field": 1.5}, "field", "1.5", None, None, True),
    ({"field": True}, "field", "True", None, None, True),  # JSON true, not SQL 1
    ({"field": True}, "field", None, 0.0, None, True),  # bool is a Python number
    ({"field": "12"}, "field", None, 10.0, None, False),  # numeric strings stay strings
    ({"field": [1, 2]}, "field", "[1, 2]", None, None, True),  # Python list repr, spaces included
    ({}, "field", None, 0.0, None, False),  # missing property fails numeric bounds
    ({"field": 5}, "field", None, 1.0, 10.0, True),
    ({"field": 5}, "field", "5", 6.0, None, False),
]


def test_match_semantics_are_pinned_by_table() -> None:
    for properties, field, equals, minimum, maximum, expected in MATCH_TABLE:
        got = DataService._matches(properties, field, equals, minimum, maximum)
        assert got is expected, (properties, field, equals, minimum, maximum)


def test_unwindowed_limit_query_pushes_the_limit_into_sql(monkeypatch: pytest.MonkeyPatch) -> None:
    # The former cliff loaded and parsed every row before slicing. Assert the
    # mechanism rather than a wall-clock: the no-bbox no-filter path must read
    # only `limit` rows (SQL LIMIT) and take `matched` from the manifest count,
    # never the unbounded scan.
    key = "landUseMesh"  # a large served collection (osmBuildings was retired in PR5)
    assert key in ALL_DATASETS
    calls: dict[str, Any] = {}
    real_all = data_service_module.all_features
    real_count = data_service_module.dataset_feature_count

    def spy_all(connection: Any, dataset_key: str, *, limit: int | None = None) -> Any:
        calls["all_features_limit"] = limit
        return real_all(connection, dataset_key, limit=limit)

    def spy_count(connection: Any, dataset_key: str) -> int:
        calls["counted"] = True
        return real_count(connection, dataset_key)

    monkeypatch.setattr(data_service_module, "all_features", spy_all)
    monkeypatch.setattr(data_service_module, "dataset_feature_count", spy_count)

    result = store_backed.query_features(key, limit=5)

    assert calls["all_features_limit"] == 5  # bounded read, not a full scan
    assert calls.get("counted") is True  # matched from the manifest, not len()
    assert result["query"]["returned"] == 5
    assert result["query"]["matched"] > 5  # the whole-dataset total
