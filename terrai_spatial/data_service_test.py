from __future__ import annotations

import json
from pathlib import Path

import pytest

from terrai_spatial.data_service import (
    DATASETS,
    FOUNDATION_DATASETS,
    HEALTH_EXCLUDED_DATASETS,
    SCENE_HANDOFFS,
    DataService,
    DatasetNotFoundError,
    service,
)


def test_health_reports_all_file_backed_datasets_ready() -> None:
    health = service.health()
    assert health["status"] == "ready"
    expected = len(DATASETS) + len(FOUNDATION_DATASETS) - len(HEALTH_EXCLUDED_DATASETS)
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
    assert catalog["kunijibanBoreholes"]["delivery"] == "on_demand"
    assert catalog["kunijibanBoreholes"]["kind"] == "asset_manifest"
    assert catalog["kunijibanBoreholes"]["feature_count"] == 11_703
    assert "kunijibanBoreholes" not in service.bootstrap()
    assert service.bootstrap()["meta"]["datasets_total"] == (
        len(DATASETS) + len(FOUNDATION_DATASETS) - len(HEALTH_EXCLUDED_DATASETS)
    )


def test_kunijiban_manifest_preserves_mixed_provenance_and_local_assets() -> None:
    manifest = service.load("kunijibanBoreholes")

    assert manifest["retrieved_at"] == "2026-06-27T13:04:00+09:00"
    assert manifest["source_updated_at"] is None
    assert manifest["evidence_status"] == "mixed_observed_and_model_extracted"
    assert manifest["provenance_counts"] == {
        "raw_xml": 6_462,
        "pdf_vlm": 5_241,
    }
    assert manifest["filters_applied"]["excluded_data_source"] == "pdf_vlm_empty"
    assert manifest["filters_applied"]["excluded_boreholes"] == 364
    assert {asset["role"] for asset in manifest["assets"]} == {
        "boreholes_nested",
        "stratigraphic_layers_flat",
        "spt_tests_flat",
    }
    assert all((service.root / relative).is_file() for relative in manifest["files"])


def test_scene_handoffs_resolve_through_existing_foundation_dataset_keys() -> None:
    assert set(SCENE_HANDOFFS) == {"uc24_16_nihonbashi", "uc24_13_sapporo"}
    assert set(SCENE_HANDOFFS).issubset(FOUNDATION_DATASETS)
    assert "undergroundScenes" not in FOUNDATION_DATASETS

    catalog = service.scene_catalog()
    assert [item["scene_id"] for item in catalog["scenes"]] == [
        "nihonbashi-utilities",
        "sapporo-station-underground",
    ]
    assert service.scene_handoff("uc24_16_nihonbashi")["scene_id"] == "nihonbashi-utilities"
    assert service.scene_handoff("uc24_13_sapporo")["scene_id"] == "sapporo-station-underground"
    assert "uc24_16_nihonbashi" not in service.bootstrap()
    assert "uc24_13_sapporo" not in service.bootstrap()

    rows = {item["key"]: item for item in service.catalog()}
    assert rows["uc24_16_nihonbashi"]["scene_handoff_ready"] is True
    assert rows["uc24_13_sapporo"]["scene_handoff_ready"] is True

    with pytest.raises(DatasetNotFoundError):
        service.scene_handoff("osmSapporoUndergroundAccess")


def test_catalog_rejects_empty_or_corrupt_scene_handoff(tmp_path: Path) -> None:
    handoff = tmp_path / SCENE_HANDOFFS["uc24_16_nihonbashi"]
    handoff.parent.mkdir(parents=True)
    local_service = DataService(tmp_path)

    handoff.write_text("", encoding="utf-8")
    rows = {item["key"]: item for item in local_service.catalog()}
    assert rows["uc24_16_nihonbashi"]["scene_handoff_ready"] is False

    handoff.write_text("{", encoding="utf-8")
    rows = {item["key"]: item for item in local_service.catalog()}
    assert rows["uc24_16_nihonbashi"]["scene_handoff_ready"] is False

    handoff.write_text("{}", encoding="utf-8")
    rows = {item["key"]: item for item in local_service.catalog()}
    assert rows["uc24_16_nihonbashi"]["scene_handoff_ready"] is True


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


def test_missing_store_and_missing_store_content_fail_loudly(tmp_path: Path) -> None:
    import sqlite3

    from terrai_spatial.store import STORE_PATH, StoreSource, build_store

    absent = DataService(tmp_path)
    with pytest.raises(RuntimeError, match="spatial store is missing"):
        absent.load("jointSummary")
    with pytest.raises(RuntimeError, match="spatial store is missing"):
        absent.require_store()

    (tmp_path / "data/joint").mkdir(parents=True)
    (tmp_path / "data/joint/joint_summary.json").write_text("{\"generated_at\": \"2026-07-20\"}", encoding="utf-8")
    build_store(
        tmp_path,
        tmp_path / STORE_PATH,
        [StoreSource("jointSummary", "data/joint/joint_summary.json", "document", "AL", "observed")],
    )
    local_service = DataService(tmp_path)
    assert local_service.load("jointSummary") == {"generated_at": "2026-07-20"}

    writable = sqlite3.connect(tmp_path / STORE_PATH)
    writable.execute("DELETE FROM documents WHERE key = 'jointSummary'")
    writable.commit()
    writable.close()
    with pytest.raises(RuntimeError, match="missing from the spatial store"):
        DataService(tmp_path).load("jointSummary")


def test_feature_query_rejects_a_dataset_that_is_not_a_feature_collection() -> None:
    with pytest.raises(ValueError, match="not a GeoJSON FeatureCollection"):
        service.query_features("jointSummary")


def test_scene_bundle_resolves_by_scene_id_through_the_catalog() -> None:
    bundle = service.scene_bundle("nihonbashi-utilities")
    assert bundle["scene"]["owner_dataset_key"] == "uc24_16_nihonbashi"
    assert bundle["handoff"]["scene_id"] == "nihonbashi-utilities"
    # The handoff passes through verbatim: unresolved families keep their
    # states and reasons, and nothing invents geometry or counts for them.
    families = bundle["handoff"]["evidence_families"]
    assert families["predicted_fields"]["availability"] == "unresolved"
    assert families["underground_structures"]["availability"] == "not_applicable"
    assert bundle["handoff"]["approved_roots"]

    sapporo = service.scene_bundle("sapporo-station-underground")
    assert sapporo["scene"]["owner_dataset_key"] == "uc24_13_sapporo"
    assert sapporo["handoff"]["evidence_families"]["utility_networks"]["availability"] == "not_applicable"


def test_scene_bundle_rejects_an_unknown_scene_id() -> None:
    with pytest.raises(DatasetNotFoundError):
        service.scene_bundle("no-such-scene")
    with pytest.raises(DatasetNotFoundError):
        # Owner dataset keys are not scene ids; the catalog is the only path.
        service.scene_bundle("uc24_16_nihonbashi")


def test_wide_products_win_per_file_and_fall_back_when_absent_or_empty(tmp_path: Path) -> None:
    from terrai_spatial.data_service import MLIT_WIDE_DIR, resolved_dataset_path

    relative = "data/mlit/railway.geojson"
    assert resolved_dataset_path(relative, tmp_path) == relative

    wide = tmp_path / MLIT_WIDE_DIR / "railway.geojson"
    wide.parent.mkdir(parents=True)
    wide.write_text('{"type":"FeatureCollection","features":[]}', encoding="utf-8")
    assert resolved_dataset_path(relative, tmp_path) == f"{MLIT_WIDE_DIR}/railway.geojson"

    # An empty file is not a product; the atomic writer never leaves one, so
    # this is a deleted-or-never-fetched state and the demo subset serves.
    wide.write_text("", encoding="utf-8")
    assert resolved_dataset_path(relative, tmp_path) == relative

    # Only the MLIT foundation paths participate in scope resolution.
    other = tmp_path / MLIT_WIDE_DIR / "resilience_hubs.geojson"
    other.write_text("{}", encoding="utf-8")
    assert resolved_dataset_path("data/joint/resilience_hubs.geojson", tmp_path) == "data/joint/resilience_hubs.geojson"


def test_store_sources_and_path_for_follow_scope_resolution(tmp_path: Path) -> None:
    from terrai_spatial.data_service import MLIT_WIDE_DIR, DataService, store_sources

    wide = tmp_path / MLIT_WIDE_DIR / "land_use_mesh.geojson"
    wide.parent.mkdir(parents=True)
    wide.write_text('{"type":"FeatureCollection","features":[]}', encoding="utf-8")

    by_key = {source.key: source for source in store_sources(tmp_path)}
    assert by_key["landUseMesh"].path == f"{MLIT_WIDE_DIR}/land_use_mesh.geojson"
    assert by_key["railway"].path == "data/mlit/railway.geojson"
    assert by_key["hubs"].path == "data/joint/resilience_hubs.geojson"

    service = DataService(tmp_path)
    assert service.path_for("landUseMesh") == wide
    assert service.path_for("railway") == tmp_path / "data/mlit/railway.geojson"
