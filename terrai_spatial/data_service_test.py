from __future__ import annotations

import json
from pathlib import Path

import pytest

from terrai_spatial.data_service import (
    ASSET_MANIFEST_DATASETS,
    DATASETS,
    FOUNDATION_DATASETS,
    DataService,
    DatasetNotFoundError,
    service,
)


def test_health_reports_all_file_backed_datasets_ready() -> None:
    health = service.health()
    assert health["status"] == "ready"
    expected = len(DATASETS) + len(FOUNDATION_DATASETS) - len(ASSET_MANIFEST_DATASETS)
    assert health["datasets_total"] == expected
    assert health["datasets_ready"] == expected


def test_foundation_datasets_are_on_demand_not_bootstrapped() -> None:
    catalog = {row["key"]: row for row in service.catalog()}
    assert catalog["landslideWarning"]["delivery"] == "on_demand"
    assert "landslideWarning" not in service.bootstrap()
    assert catalog["uc24_16_nihonbashi"]["delivery"] == "on_demand"
    assert "uc24_16_nihonbashi" not in service.bootstrap()
    assert catalog["uc24_13_sapporo"]["delivery"] == "on_demand"
    assert "uc24_13_sapporo" not in service.bootstrap()
    assert catalog["osmSapporoUndergroundAccess"]["delivery"] == "on_demand"
    assert "osmSapporoUndergroundAccess" not in service.bootstrap()
    assert service.bootstrap()["meta"]["datasets_total"] == (
        len(DATASETS) + len(FOUNDATION_DATASETS) - len(ASSET_MANIFEST_DATASETS)
    )


def test_asset_manifest_readiness_requires_every_local_cache_file(tmp_path: Path) -> None:
    manifest = tmp_path / "data/plateau/uc24_16_nihonbashi/manifest.json"
    asset = tmp_path / "data/external/plateau_uc24_16/assets/water-pipe/tileset.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        '{"feature_count": 1, "files": ["data/external/plateau_uc24_16/assets/water-pipe/tileset.json"], '
        '"resources": [{"tileset_url": "/api/v1/assets/external/plateau_uc24_16/assets/water-pipe/tileset.json"}]}',
        encoding="utf-8",
    )
    local_service = DataService(tmp_path)

    row = next(item for item in local_service.catalog() if item["key"] == "uc24_16_nihonbashi")
    assert row["ready"] is False
    assert row["feature_count"] == 1

    asset.parent.mkdir(parents=True)
    asset.write_text("{", encoding="utf-8")
    row = next(item for item in local_service.catalog() if item["key"] == "uc24_16_nihonbashi")
    assert row["ready"] is False

    asset.write_text("{}", encoding="utf-8")
    row = next(item for item in local_service.catalog() if item["key"] == "uc24_16_nihonbashi")
    assert row["ready"] is True
    assert row["asset_roots"] == [
        "/api/v1/assets/external/plateau_uc24_16/assets/water-pipe/tileset.json"
    ]


def test_sapporo_asset_manifest_exposes_two_independent_asset_roots(tmp_path: Path) -> None:
    manifest = tmp_path / "data/plateau/uc24_13_sapporo/manifest.json"
    mall = tmp_path / "data/external/plateau_uc24_13/assets/mall/tileset.json"
    station = tmp_path / "data/external/plateau_uc24_13/assets/station/tileset.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        json.dumps(
            {
                "feature_count": 3,
                "files": [str(mall.relative_to(tmp_path)), str(station.relative_to(tmp_path))],
                "resources": [
                    {"tileset_url": "/api/v1/assets/external/plateau_uc24_13/assets/mall/tileset.json"},
                    {"tileset_url": "/api/v1/assets/external/plateau_uc24_13/assets/station/tileset.json"},
                ],
            }
        ),
        encoding="utf-8",
    )
    mall.parent.mkdir(parents=True)
    mall.write_text("{}", encoding="utf-8")
    station.parent.mkdir(parents=True)
    station.write_text("{}", encoding="utf-8")

    row = next(item for item in DataService(tmp_path).catalog() if item["key"] == "uc24_13_sapporo")

    assert row["ready"] is True
    assert row["feature_count"] == 3
    assert len(row["asset_roots"]) == 2


def test_bootstrap_contains_ranked_server_side_recommendations() -> None:
    payload = service.bootstrap()
    assert payload["meta"]["api_version"] == "v1"
    assert "facilitySummary" in payload

    slope = payload["recommendations"]["slope"]["features"]
    assert slope
    scores = [feature["properties"]["risk_score"] for feature in slope]
    assert scores == sorted(scores, reverse=True)
    assert all(feature["properties"]["risk_band"] == "high" for feature in slope)

    yokohama = payload["recommendations"]["embeddingYokohama"]["features"]
    mobara = payload["recommendations"]["embeddingMobara"]["features"]
    assert all(feature["properties"]["region"] == "yokohama" for feature in yokohama)
    assert all(feature["properties"]["region"] == "mobara" for feature in mobara)


def test_feature_query_filters_sorts_and_limits() -> None:
    result = service.query_features(
        "solar",
        where="status",
        equals="preferred",
        sort="score",
        descending=True,
        limit=3,
    )
    assert result["query"]["returned"] == 3
    scores = [feature["properties"]["score"] for feature in result["features"]]
    assert scores == sorted(scores, reverse=True)
    assert all(feature["properties"]["status"] == "preferred" for feature in result["features"])


def test_unknown_dataset_key_is_rejected() -> None:
    with pytest.raises(DatasetNotFoundError):
        service.load("no-such-dataset")


def test_feature_query_rejects_a_dataset_that_is_not_a_feature_collection() -> None:
    with pytest.raises(ValueError, match="not a GeoJSON FeatureCollection"):
        service.query_features("jointSummary")
