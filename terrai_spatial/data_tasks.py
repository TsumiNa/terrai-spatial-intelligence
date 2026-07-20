"""Declarative data-task registry shared by the CLI and automatic startup."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class DataTask:
    name: str
    description: str
    script: str
    inputs: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()
    output_globs: tuple[str, ...] = ()
    cache_outputs: tuple[str, ...] = ()
    manifest: str | None = None
    dependencies: tuple[str, ...] = ()
    network: bool = False
    remote_extra: bool = False
    automatic: bool = True
    force_argument: bool = False
    offline_argument: bool = False
    check_stale: bool = True
    repair_missing_cache: bool = False


@dataclass(frozen=True)
class TaskState:
    name: str
    status: str
    reason: str


BOOTSTRAP_OUTPUTS = (
    "data/external/source_registry.json",
    "data/external/yokohama/hinanjo_20260401.csv",
    "data/yokohama/building_risk.geojson",
    "data/yokohama/building_summary.json",
    "data/yokohama/road_priority.geojson",
    "data/yokohama/road_summary.json",
    "data/mobara/context.geojson",
    "data/mobara/site_cells.geojson",
    "data/mobara/solar_summary.json",
)

EMBEDDING_OUTPUTS = (
    "data/google/satellite_embedding/embedding_evidence.geojson",
    "data/google/satellite_embedding/summary.json",
    "data/google/satellite_embedding/yokohama_change_2023_2024.png",
    "data/google/satellite_embedding/yokohama_latent_2024.png",
    "data/google/satellite_embedding/mobara_change_2023_2024.png",
    "data/google/satellite_embedding/mobara_latent_2024.png",
)

TASKS = {
    "bootstrap": DataTask(
        "bootstrap",
        "restore packaged source snapshots from Git HEAD or the TerrAI repository",
        "scripts/bootstrap_packaged_data.py",
        outputs=BOOTSTRAP_OUTPUTS,
        force_argument=True,
        offline_argument=True,
        check_stale=False,
    ),
    "tiles": DataTask(
        "tiles",
        "cache GSI standard, imagery, relief and slope tiles",
        "scripts/fetch_visual_tiles.py",
        outputs=("data/tiles/manifest.json",),
        manifest="data/tiles/manifest.json",
        network=True,
        force_argument=True,
    ),
    "embedding": DataTask(
        "embedding",
        "fetch and process Google Satellite Embedding crops",
        "scripts/fetch_google_satellite_embedding.py",
        outputs=EMBEDDING_OUTPUTS,
        network=True,
        remote_extra=True,
    ),
    "grid": DataTask(
        "grid",
        "download the local-only TEPCO cache when needed and rebuild its screen",
        "scripts/update_tepco_grid.py",
        outputs=("data/mobara/tepco_grid_screen.json",),
        cache_outputs=(
            "data/external/tepco/csv_yosochoryu_chiba_soudensen.csv",
            "data/external/tepco/csv_yosochoryu_chiba_hendensyo.csv",
            "data/external/tepco/download_metadata.local.json",
        ),
        force_argument=True,
        offline_argument=True,
        check_stale=False,
        repair_missing_cache=True,
    ),
    "joint": DataTask(
        "joint",
        "rebuild cross-module hubs, corridors and solar delivery cells",
        "scripts/build_joint_analysis.py",
        inputs=(
            "data/yokohama/building_risk.geojson",
            "data/yokohama/road_priority.geojson",
            "data/mobara/site_cells.geojson",
        ),
        outputs=(
            "data/joint/compound_corridors.geojson",
            "data/joint/resilience_hubs.geojson",
            "data/joint/solar_delivery_cells.geojson",
            "data/joint/joint_summary.json",
        ),
        dependencies=("bootstrap",),
    ),
    "evidence": DataTask(
        "evidence",
        "rebuild official-facility and multi-scale evidence products",
        "scripts/build_multiscale_evidence.py",
        inputs=(
            "data/yokohama/building_risk.geojson",
            "data/yokohama/road_priority.geojson",
            "data/mobara/site_cells.geojson",
            "data/external/yokohama/hinanjo_20260401.csv",
            "data/google/satellite_embedding/embedding_evidence.geojson",
        ),
        outputs=(
            "data/yokohama/official_facility_resilience.geojson",
            "data/evidence/yokohama_zones.geojson",
            "data/evidence/mobara_zones.geojson",
            "data/evidence/multiscale_summary.json",
        ),
        dependencies=("bootstrap", "embedding"),
    ),
}


def _valid_file(path: Path) -> bool:
    if not path.is_file() or path.stat().st_size == 0:
        return False
    if path.suffix not in {".json", ".geojson"}:
        return True
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return path.suffix != ".geojson" or value.get("type") == "FeatureCollection"


def _existing_outputs(task: DataTask, root: Path) -> tuple[list[Path], list[str]]:
    paths = [root / item for item in task.outputs]
    missing = [item for item, path in zip(task.outputs, paths, strict=True) if not _valid_file(path)]
    for pattern in task.output_globs:
        matches = [path for path in root.glob(pattern) if path.is_file() and path.stat().st_size > 0]
        paths.extend(matches)
        if not matches:
            missing.append(pattern)
    if task.manifest and _valid_file(root / task.manifest):
        manifest = json.loads((root / task.manifest).read_text(encoding="utf-8"))
        manifest_files = manifest.get("files", [])
        if not manifest_files:
            missing.append(f"{task.manifest}:files")
        for relative in manifest_files:
            path = (root / relative).resolve()
            if root.resolve() not in path.parents:
                missing.append(f"{task.manifest}:unsafe path {relative}")
                continue
            paths.append(path)
            if not _valid_file(path):
                missing.append(relative)
    return paths, missing


def task_state(name: str, root: Path = ROOT) -> TaskState:
    task = TASKS[name]
    outputs, missing_outputs = _existing_outputs(task, root)
    missing_inputs = [item for item in task.inputs if not (root / item).is_file()]
    if missing_outputs:
        if missing_inputs:
            return TaskState(name, "blocked", f"missing inputs: {', '.join(missing_inputs)}")
        return TaskState(name, "missing", f"missing outputs: {', '.join(missing_outputs)}")
    if missing_inputs:
        return TaskState(name, "ready", "outputs are present; optional rebuild inputs are unavailable")
    missing_cache = [item for item in task.cache_outputs if not _valid_file(root / item)]
    if missing_cache:
        return TaskState(name, "ready", f"derived output is present; local cache missing: {', '.join(missing_cache)}")
    if task.network or not task.check_stale or not outputs:
        return TaskState(name, "ready", "cached outputs are present")
    source_paths = [root / task.script, *(root / item for item in task.inputs)]
    newest_input = max(path.stat().st_mtime for path in source_paths if path.exists())
    oldest_output = min(path.stat().st_mtime for path in outputs)
    if newest_input > oldest_output:
        return TaskState(name, "stale", "a script or input is newer than an output")
    return TaskState(name, "ready", "outputs are complete and current")


def _ordered_names(selected: list[str] | None) -> list[str]:
    requested = selected or [name for name, task in TASKS.items() if task.automatic]
    unknown = sorted(set(requested) - set(TASKS))
    if unknown:
        raise ValueError(f"Unknown data task(s): {', '.join(unknown)}")
    ordered: list[str] = []

    def add(name: str) -> None:
        for dependency in TASKS[name].dependencies:
            add(dependency)
        if name not in ordered:
            ordered.append(name)

    for name in requested:
        add(name)
    return ordered


def _run(task: DataTask, root: Path, force: bool, allow_network: bool) -> None:
    script = root / task.script
    if task.remote_extra:
        uv = shutil.which("uv")
        if not uv:
            raise RuntimeError("uv is required to install the remote-data extras")
        command = [uv, "run", "--extra", "remote", "python", str(script)]
    else:
        command = [sys.executable, str(script)]
    if force and task.force_argument:
        command.append("--force")
    if not allow_network and task.offline_argument:
        command.append("--offline")
    print(f"[TerrAI data] running {task.name}: {task.description}", flush=True)
    subprocess.run(command, cwd=root, check=True)


def ensure_data(
    *,
    root: Path = ROOT,
    selected: list[str] | None = None,
    allow_network: bool = True,
    force: bool = False,
) -> list[TaskState]:
    results: list[TaskState] = []
    for name in _ordered_names(selected):
        task = TASKS[name]
        state = task_state(name, root)
        missing_cache = [item for item in task.cache_outputs if not _valid_file(root / item)]
        if state.status == "blocked":
            raise RuntimeError(f"{name} cannot run: {state.reason}")
        force_requested = force and (
            (selected is None and name != "bootstrap")
            or (selected is not None and name in selected)
        )
        should_run = force_requested
        should_run = should_run or state.status in {"missing", "stale"}
        should_run = should_run or (task.repair_missing_cache and allow_network and bool(missing_cache))
        if not should_run:
            print(f"[TerrAI data] {name}: {state.status} — {state.reason}", flush=True)
            results.append(state)
            continue
        if task.network and not allow_network:
            raise RuntimeError(f"{name} requires network access: {state.reason}")
        missing_inputs = [item for item in task.inputs if not (root / item).is_file()]
        if missing_inputs:
            raise RuntimeError(f"{name} cannot run; missing inputs: {', '.join(missing_inputs)}")
        _run(task, root, force, allow_network)
        refreshed = task_state(name, root)
        if refreshed.status not in {"ready"}:
            raise RuntimeError(f"{name} did not produce complete data: {refreshed.reason}")
        results.append(refreshed)
    return results


def status_rows(root: Path = ROOT) -> list[TaskState]:
    return [task_state(name, root) for name in TASKS]


def validate_json_outputs(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    for task in TASKS.values():
        for relative in task.outputs:
            path = root / relative
            if path.suffix not in {".json", ".geojson"} or not path.is_file():
                continue
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
                if path.suffix == ".geojson" and value.get("type") != "FeatureCollection":
                    failures.append(f"invalid GeoJSON root: {relative}")
            except (OSError, json.JSONDecodeError) as error:
                failures.append(f"invalid {relative}: {error}")
    return failures
