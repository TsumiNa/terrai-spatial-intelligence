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
)
from terrai_spatial.store_test import scan_intersects


class FileBackedOracle(DataService):
    """The pre-store service: raw files, linear scans, per-access copies."""

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
SAPPORO_WINDOW = (141.350, 43.055, 141.357, 43.071)

QUERY_MATRIX = [
    {"key": "landHistory", "bbox": YOKOHAMA_WINDOW},
    {"key": "landUseMesh", "bbox": YOKOHAMA_WINDOW, "where": "terrai_region", "equals": "yokohama"},
    {"key": "landUseMesh", "where": "terrai_region", "equals": "mobara", "limit": 500},
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
]


def test_every_dataset_loads_byte_identically_from_the_store() -> None:
    for key in ALL_DATASETS:
        assert canonical(store_backed.load(key)) == canonical(oracle.load(key)), key


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
