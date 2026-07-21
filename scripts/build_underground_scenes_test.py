from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path

import pytest

from scripts.build_underground_scenes import (
    EVIDENCE_FAMILIES,
    HANDOFF_PATHS,
    build_scene_handoffs,
    local_to_world,
    validate_handoff,
    world_to_local,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUTS = (
    "data/plateau/uc24_16_nihonbashi/manifest.json",
    "data/plateau/uc24_16_nihonbashi/audit_index.json",
    "data/plateau/uc24_13_sapporo/manifest.json",
    "data/osm/sapporo_underground_access/metadata.json",
    "data/osm/sapporo_underground_access/features.geojson",
)


def copy_inputs(root: Path) -> None:
    for relative in INPUTS:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PROJECT_ROOT / relative, target)


def test_builds_deterministic_isolated_scene_handoffs(tmp_path: Path) -> None:
    copy_inputs(tmp_path)

    catalog = build_scene_handoffs(tmp_path)
    first_bytes = {
        scene_id: (tmp_path / relative).read_bytes()
        for scene_id, relative in HANDOFF_PATHS.items()
    }
    build_scene_handoffs(tmp_path)

    assert [item["scene_id"] for item in catalog["scenes"]] == [
        "nihonbashi-utilities",
        "sapporo-station-underground",
    ]
    assert first_bytes == {
        scene_id: (tmp_path / relative).read_bytes()
        for scene_id, relative in HANDOFF_PATHS.items()
    }

    nihonbashi = json.loads(first_bytes["nihonbashi-utilities"])
    sapporo = json.loads(first_bytes["sapporo-station-underground"])
    assert set(nihonbashi["evidence_families"]) == set(EVIDENCE_FAMILIES)
    assert nihonbashi["evidence_families"]["utility_networks"]["sources"][0]["feature_count"] == 810
    assert sapporo["evidence_families"]["underground_structures"]["sources"][0]["feature_count"] == 70_718
    assert nihonbashi["evidence_families"]["underground_structures"]["availability"] == "not_applicable"
    assert sapporo["evidence_families"]["utility_networks"]["availability"] == "not_applicable"
    assert "plateau_uc24_13_sapporo" not in json.dumps(nihonbashi)
    assert "plateau_uc24_16_nihonbashi" not in json.dumps(sapporo)
    assert "synthetic" not in json.dumps([nihonbashi, sapporo]).lower()


def test_local_frame_round_trips_height_and_horizontal_coordinates(tmp_path: Path) -> None:
    copy_inputs(tmp_path)
    build_scene_handoffs(tmp_path)
    handoff = json.loads((tmp_path / HANDOFF_PATHS["sapporo-station-underground"]).read_text())
    frame = handoff["local_frame"]
    point = (141.353, 43.061, 51.25)

    local = world_to_local(frame, *point)
    recovered = local_to_world(frame, local)

    assert recovered[0] == pytest.approx(point[0], abs=1e-8)
    assert recovered[1] == pytest.approx(point[1], abs=1e-8)
    assert recovered[2] == pytest.approx(point[2], abs=1e-4)
    assert frame["orthometric_vertical_datum"] == "unknown"


def test_unavailable_evidence_cannot_carry_fake_counts_or_models(tmp_path: Path) -> None:
    copy_inputs(tmp_path)
    build_scene_handoffs(tmp_path)
    handoff = json.loads((tmp_path / HANDOFF_PATHS["nihonbashi-utilities"]).read_text())
    invalid = copy.deepcopy(handoff)
    invalid["evidence_families"]["predicted_fields"]["feature_count"] = 1

    with pytest.raises(RuntimeError, match="fabricated metadata"):
        validate_handoff(invalid)


def test_available_assets_cannot_escape_scene_approved_roots(tmp_path: Path) -> None:
    copy_inputs(tmp_path)
    build_scene_handoffs(tmp_path)
    handoff = json.loads((tmp_path / HANDOFF_PATHS["nihonbashi-utilities"]).read_text())
    handoff["evidence_families"]["utility_networks"]["sources"][0]["asset_paths"] = [
        "data/external/plateau_uc24_13/assets/wrong/tileset.json"
    ]

    with pytest.raises(RuntimeError, match="escapes its approved scene roots"):
        validate_handoff(handoff)


def test_mismatched_source_scene_id_stops_cross_scene_join(tmp_path: Path) -> None:
    copy_inputs(tmp_path)
    metadata_path = tmp_path / "data/osm/sapporo_underground_access/metadata.json"
    metadata = json.loads(metadata_path.read_text())
    metadata["scene_id"] = "nihonbashi-utilities"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    with pytest.raises(RuntimeError, match="preserve Nihonbashi/Sapporo isolation"):
        build_scene_handoffs(tmp_path)


def test_osm_metadata_feature_count_must_match_snapshot(tmp_path: Path) -> None:
    copy_inputs(tmp_path)
    metadata_path = tmp_path / "data/osm/sapporo_underground_access/metadata.json"
    metadata = json.loads(metadata_path.read_text())
    metadata["feature_count"] += 1
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    with pytest.raises(RuntimeError, match="OSM feature_count metadata is 196; snapshot contains 195"):
        build_scene_handoffs(tmp_path)
