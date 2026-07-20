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
