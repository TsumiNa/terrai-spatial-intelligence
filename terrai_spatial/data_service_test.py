from __future__ import annotations

import pytest

from terrai_spatial.data_service import DATASETS, FOUNDATION_DATASETS, DatasetNotFoundError, service


def test_health_reports_all_file_backed_datasets_ready() -> None:
    health = service.health()
    assert health["status"] == "ready"
    assert health["datasets_ready"] == len(DATASETS) + len(FOUNDATION_DATASETS)
    assert health["datasets_total"] == len(DATASETS) + len(FOUNDATION_DATASETS)


def test_foundation_datasets_are_on_demand_not_bootstrapped() -> None:
    catalog = {row["key"]: row for row in service.catalog()}
    assert catalog["landslideWarning"]["delivery"] == "on_demand"
    assert "landslideWarning" not in service.bootstrap()


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
