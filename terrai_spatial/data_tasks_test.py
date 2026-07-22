from __future__ import annotations

import json
import os
import shutil
import sys
import zipfile
from pathlib import Path

import pytest

from terrai_spatial.data_tasks import (
    BOOTSTRAP_OUTPUTS,
    TASKS,
    _run,
    _ordered_names,
    ensure_data,
    task_state,
    validate_json_outputs,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def write_json(path: Path, *, geojson: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    value = {"type": "FeatureCollection", "features": []} if geojson else {}
    path.write_text(json.dumps(value), encoding="utf-8")


def test_joint_missing_and_stale_outputs_are_detected(tmp_path: Path) -> None:
    script = tmp_path / "scripts/build_joint_analysis.py"
    script.parent.mkdir(parents=True)
    script.write_text("# test\n", encoding="utf-8")
    inputs = (
        "data/yokohama/building_risk.geojson",
        "data/yokohama/road_priority.geojson",
        "data/mobara/site_cells.geojson",
    )
    outputs = (
        "data/joint/compound_corridors.geojson",
        "data/joint/resilience_hubs.geojson",
        "data/joint/solar_delivery_cells.geojson",
        "data/joint/joint_summary.json",
    )
    for relative in inputs:
        write_json(tmp_path / relative, geojson=True)
    for relative in outputs:
        write_json(tmp_path / relative, geojson=relative.endswith(".geojson"))
    for path in [script, *(tmp_path / item for item in inputs)]:
        os.utime(path, (100, 100))
    for path in (tmp_path / item for item in outputs):
        os.utime(path, (200, 200))

    assert task_state("joint", tmp_path).status == "ready"
    os.utime(tmp_path / inputs[0], (300, 300))
    assert task_state("joint", tmp_path).status == "stale"
    (tmp_path / outputs[0]).unlink()
    assert task_state("joint", tmp_path).status == "missing"


def test_tile_manifest_detects_a_missing_cached_file(tmp_path: Path) -> None:
    tile = tmp_path / "data/tiles/yokohama/15/1-1.png"
    tile.parent.mkdir(parents=True)
    tile.write_bytes(b"valid tile")
    manifest = tmp_path / "data/tiles/manifest.json"
    manifest.write_text(json.dumps({"files": [str(tile.relative_to(tmp_path))]}), encoding="utf-8")

    assert task_state("tiles", tmp_path).status == "ready"
    tile.unlink()
    state = task_state("tiles", tmp_path)
    assert state.status == "missing"
    assert "1-1.png" in state.reason


def test_corrupt_packaged_json_is_incomplete(tmp_path: Path) -> None:
    for relative in BOOTSTRAP_OUTPUTS:
        path = tmp_path / relative
        if path.suffix == ".csv":
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("header\n", encoding="utf-8")
        else:
            write_json(path, geojson=path.suffix == ".geojson")
    (tmp_path / "data/mobara/solar_summary.json").write_text("{", encoding="utf-8")

    assert task_state("bootstrap", tmp_path).status == "missing"


def test_evidence_dependencies_are_ordered_before_the_task() -> None:
    assert _ordered_names(["evidence"]) == ["bootstrap", "embedding", "gsi_evacuation", "evidence"]


def test_missing_local_grid_cache_runs_download_even_when_summary_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    for name in ("fetch_tepco_grid.py", "parse_tepco_grid.py", "update_tepco_grid.py"):
        shutil.copy2(PROJECT_ROOT / "scripts" / name, scripts / name)
    source = tmp_path / "tepco-fixture.zip"
    preamble = "\n".join(["metadata"] * 6) + "\n"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("csv_yosochoryu_chiba_soudensen.csv", preamble)
        archive.writestr("csv_yosochoryu_chiba_hendensyo.csv", preamble)
    write_json(tmp_path / "data/mobara/tepco_grid_screen.json")

    monkeypatch.setenv("TERRAI_TEPCO_CHIBA_URL", source.as_uri())
    # The sandbox relocates the scripts but not the shared pipeline library;
    # resolve it from the real repository, as any checkout does.
    monkeypatch.setenv("PYTHONPATH", str(PROJECT_ROOT))
    states = ensure_data(root=tmp_path, selected=["grid"], allow_network=True)

    assert states[-1].status == "ready"
    output = tmp_path / "data/mobara/tepco_grid_screen.json"
    assert output.is_file()
    screen = json.loads(output.read_text(encoding="utf-8"))
    assert screen["chiba_summary"]["transmission_line_rows"] == 0
    assert (tmp_path / "data/external/tepco/download_metadata.local.json").is_file()


def test_offline_start_accepts_committed_grid_summary_without_local_cache(tmp_path: Path) -> None:
    write_json(tmp_path / "data/mobara/tepco_grid_screen.json")

    states = ensure_data(root=tmp_path, selected=["grid"], allow_network=False)

    assert states[-1].status == "ready"
    assert "local cache missing" in states[-1].reason


def test_underground_scene_requires_every_manifest_cache_file(tmp_path: Path) -> None:
    source_manifest = tmp_path / "data/plateau/uc24_16_nihonbashi/source_manifest.json"
    retrieval_manifest = tmp_path / "data/plateau/uc24_16_nihonbashi/manifest.json"
    audit_index = tmp_path / "data/plateau/uc24_16_nihonbashi/audit_index.json"
    cache_file = tmp_path / "data/external/plateau_uc24_16/assets/water-pipe/tileset.json"
    write_json(source_manifest)
    retrieval_manifest.parent.mkdir(parents=True, exist_ok=True)
    retrieval_manifest.write_text(
        json.dumps({"files": [str(cache_file.relative_to(tmp_path))]}), encoding="utf-8"
    )
    write_json(audit_index)

    state = task_state("underground_utilities", tmp_path)
    assert state.status == "missing"
    assert "water-pipe/tileset.json" in state.reason

    write_json(cache_file)
    assert task_state("underground_utilities", tmp_path).status == "ready"


def test_offline_incomplete_underground_scene_is_not_reported_ready(tmp_path: Path) -> None:
    write_json(tmp_path / "data/plateau/uc24_16_nihonbashi/source_manifest.json")
    write_json(tmp_path / "data/plateau/uc24_16_nihonbashi/manifest.json")
    write_json(tmp_path / "data/plateau/uc24_16_nihonbashi/audit_index.json")

    with pytest.raises(RuntimeError, match="requires network access"):
        ensure_data(root=tmp_path, selected=["underground_utilities"], allow_network=False)


def test_sapporo_structure_scene_requires_every_manifest_cache_file(tmp_path: Path) -> None:
    source_manifest = tmp_path / "data/plateau/uc24_13_sapporo/source_manifest.json"
    retrieval_manifest = tmp_path / "data/plateau/uc24_13_sapporo/manifest.json"
    cache_file = tmp_path / "data/external/plateau_uc24_13/assets/sapporo-underground-mall/tileset.json"
    write_json(source_manifest)
    retrieval_manifest.parent.mkdir(parents=True, exist_ok=True)
    retrieval_manifest.write_text(
        json.dumps({"files": [str(cache_file.relative_to(tmp_path))]}), encoding="utf-8"
    )

    state = task_state("underground_structures", tmp_path)
    assert state.status == "missing"
    assert "sapporo-underground-mall/tileset.json" in state.reason

    write_json(cache_file)
    assert task_state("underground_structures", tmp_path).status == "ready"


def test_osm_underground_snapshot_is_explicit_refresh_not_startup_download() -> None:
    task = TASKS["underground_access_osm"]

    assert task.network is True
    assert task.automatic is False
    assert task.outputs == (
        "data/osm/sapporo_underground_access/features.geojson",
        "data/osm/sapporo_underground_access/metadata.json",
    )


def test_underground_scene_handoffs_are_offline_derived_on_demand() -> None:
    task = TASKS["underground_scenes"]

    assert task.network is False
    assert task.automatic is False
    assert task.script == "scripts/build_underground_scenes.py"
    assert task.outputs == (
        "data/scenes/underground/catalog.json",
        "data/plateau/uc24_16_nihonbashi/scene_handoff.json",
        "data/plateau/uc24_13_sapporo/scene_handoff.json",
    )


def test_integrated_fl_sources_require_retrieval_and_source_time_metadata(tmp_path: Path) -> None:
    registry = tmp_path / "data/external/source_registry.json"
    registry.parent.mkdir(parents=True)
    registry.write_text(
        json.dumps(
            {
                "sources": [
                    {"id": "complete", "status": "integrated", "retrieved_at": "2026-07-21", "source_updated_at": "2026-01-16"},
                    {"id": "unknown-explained", "status": "integrated", "retrieved_at": "2026-07-21", "source_updated_at": None, "source_updated_at_note": "continuous source"},
                    {"id": "missing-retrieval", "status": "integrated", "source_updated_at": "2026-01-16"},
                    {"id": "missing-source-time", "status": "integrated", "retrieved_at": "2026-07-21"},
                ]
            }
        ),
        encoding="utf-8",
    )

    failures = validate_json_outputs(tmp_path)

    assert failures == [
        "integrated FL source lacks retrieved_at: missing-retrieval",
        "integrated FL source lacks source_updated_at: missing-source-time",
    ]


def test_every_task_runs_on_the_current_interpreter(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No task may shell out to a package manager.

    Pipelines used to run under `uv run --extra remote`, which installed the
    geospatial stack mid-startup whenever an output went missing. The stack is
    a base dependency now, so a missing output must never trigger an install.

    `_run` is called directly rather than through `ensure_data`: a task with
    dependencies would otherwise stop at the first dependency and never reach
    the one under test, letting the assertions pass without running.
    """
    commands: list[list[str]] = []
    monkeypatch.setattr(
        "terrai_spatial.data_tasks.subprocess.run",
        lambda command, **kwargs: commands.append([str(part) for part in command]),
    )

    for name, task in TASKS.items():
        commands.clear()
        _run(task, tmp_path, force=True, allow_network=True)

        assert len(commands) == 1, f"{name} did not run exactly one command"
        command = commands[0]
        assert command[0] == sys.executable, f"{name} did not use the current interpreter"
        assert Path(command[1]).name == Path(task.script).name, name
        assert "--extra" not in command and "--group" not in command, name


def test_optional_task_with_absent_outputs_is_a_valid_steady_state(tmp_path: Path) -> None:
    task = TASKS["mlit_wide"]
    assert task.optional is True and task.automatic is False and task.network is True

    state = task_state("mlit_wide", tmp_path)
    assert state.status == "optional"
    assert "opt-in" in state.reason

    write_json(tmp_path / task.outputs[0])
    assert task_state("mlit_wide", tmp_path).status == "ready"


def test_optional_task_runs_only_when_explicitly_selected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    script = tmp_path / TASKS["mlit_wide"].script
    script.parent.mkdir(parents=True)
    script.write_text("# test\n", encoding="utf-8")
    ran: list[str] = []

    def fake_run(task, root, force, allow_network):  # noqa: ANN001 - test double
        ran.append(task.name)
        write_json(root / task.outputs[0])

    monkeypatch.setattr("terrai_spatial.data_tasks._run", fake_run)

    ensure_data(root=tmp_path, selected=["mlit_wide"], allow_network=True)
    assert ran == ["mlit_wide"]

    (tmp_path / TASKS["mlit_wide"].outputs[0]).unlink()
    ran.clear()
    with pytest.raises(RuntimeError):
        # The unselected run still fails on unrelated missing tasks, but the
        # optional task itself must not be attempted.
        ensure_data(root=tmp_path, selected=None, allow_network=False)
    assert "mlit_wide" not in ran


def test_optional_never_hides_corruption_or_blocked_states(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # A present-but-invalid output is corruption, not an unfetched cache.
    task = TASKS["mlit_wide"]
    invalid = tmp_path / task.outputs[0]
    invalid.parent.mkdir(parents=True)
    invalid.write_text("{ not json", encoding="utf-8")
    assert task_state("mlit_wide", tmp_path).status == "missing"

    # Missing inputs take precedence over the opt-in state.
    from terrai_spatial.data_tasks import DataTask

    monkeypatch.setitem(
        TASKS,
        "optional_with_inputs",
        DataTask(
            "optional_with_inputs",
            "test double",
            "scripts/none.py",
            inputs=("data/never/exists.json",),
            outputs=("data/never/output.json",),
            optional=True,
        ),
    )
    assert task_state("optional_with_inputs", tmp_path).status == "blocked"
