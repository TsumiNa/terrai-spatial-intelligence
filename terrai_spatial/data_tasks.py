"""Declarative data-task registry shared by the CLI and automatic startup."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from .data_service import store_sources
from .pipeline.io import json_file_failure, valid_data_file
from .store import STORE_PATH


ROOT = Path(__file__).resolve().parents[1]

STORE_INPUTS = tuple(sorted({source.path for source in store_sources()}))


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

# Only the manifest is declared: readiness checks parse declared JSON outputs
# in full, and the Kanto GeoJSON products are gigabyte-scale. The store build
# is the loud validator of the products themselves, and its inputs
# (STORE_INPUTS) still name every product file for staleness.
MLIT_OUTPUTS = ("data/mlit/metadata.json",)

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
    "embedding": DataTask(
        "embedding",
        "fetch and process Google Satellite Embedding crops",
        "scripts/fetch_google_satellite_embedding.py",
        outputs=EMBEDDING_OUTPUTS,
        network=True,
    ),
    "gsi_evacuation": DataTask(
        "gsi_evacuation",
        "download and normalize GSI designated evacuation data for Yokohama",
        "scripts/fetch_gsi_evacuation.py",
        outputs=(
            "data/external/gsi_evacuation/yokohama_evacuation.geojson",
            "data/external/gsi_evacuation/metadata.json",
        ),
        network=True,
        force_argument=True,
        check_stale=False,
    ),
    "mlit": DataTask(
        "mlit",
        "download and subset open MLIT foundation datasets for the Kanto window",
        "scripts/fetch_mlit_foundation.py",
        outputs=MLIT_OUTPUTS,
        network=True,
        force_argument=True,
        check_stale=False,
    ),
    "osm_kanto": DataTask(
        "osm_kanto",
        "extract mainland-Kanto OSM building footprints from the pinned snapshot",
        "scripts/fetch_osm_kanto_buildings.py",
        # Only the manifest is declared: the streamed product is gigabyte-scale
        # and declared JSON outputs are parsed in full on every status check.
        outputs=("data/osm/kanto_buildings/metadata.json",),
        network=True,
        force_argument=True,
        check_stale=False,
    ),
    "fgd_kanto": DataTask(
        "fgd_kanto",
        "normalize the pinned 基盤地図情報 Kanto building outlines into footprints",
        "scripts/fetch_fgd_kanto_buildings.py",
        # Registration-gated manual source: the committed pin is the reproducibility
        # input; the archive under source/ is dropped in by hand and never fetched.
        inputs=("data/fgd/kanto_buildings/source_manifest.json",),
        # Only the small manifests are declared: the streamed buildings.geojson is
        # gigabyte-scale and declared JSON outputs are parsed in full on every
        # status check. coverage.json is the mainland-mesh footprint the merge and
        # the map boundary consume.
        outputs=(
            "data/fgd/kanto_buildings/metadata.json",
            "data/fgd/kanto_buildings/coverage.json",
        ),
        automatic=False,
        force_argument=True,
        check_stale=False,
    ),
    "merged_tiles": DataTask(
        "merged_tiles",
        "merge OSM (primary) + 基盤地図情報 (fill) buildings into one PMTiles source",
        "scripts/merge_kanto_buildings.py",
        # The merge reads both gigabyte acquisitions and the FGD coverage footprint.
        inputs=(
            "data/osm/kanto_buildings/metadata.json",
            "data/fgd/kanto_buildings/coverage.json",
        ),
        # Only the manifest is declared: merged.geojsonl and buildings.pmtiles are
        # gigabyte-scale build products (gitignored, regenerable from the sources).
        outputs=("data/tiles/kanto_buildings/metadata.json",),
        automatic=False,
        force_argument=True,
        check_stale=False,
    ),
    "ci_fixture": DataTask(
        "ci_fixture",
        "derive the committed CI fixture windows from the full Kanto acquisitions",
        "scripts/build_ci_fixture.py",
        inputs=("data/mlit/metadata.json", "data/osm/kanto_buildings/metadata.json"),
        outputs=("data/mlit_fixture/metadata.json", "data/osm_kanto_fixture/metadata.json"),
        automatic=False,
        force_argument=True,
        check_stale=False,
    ),
    "underground_utilities": DataTask(
        "underground_utilities",
        "restore and audit the PLATEAU UC24-16 Nihonbashi utility scene",
        "scripts/fetch_plateau_uc24_16.py",
        inputs=("data/plateau/uc24_16_nihonbashi/source_manifest.json",),
        outputs=(
            "data/plateau/uc24_16_nihonbashi/manifest.json",
            "data/plateau/uc24_16_nihonbashi/audit_index.json",
        ),
        manifest="data/plateau/uc24_16_nihonbashi/manifest.json",
        network=True,
        force_argument=True,
        offline_argument=True,
        check_stale=False,
    ),
    "underground_structures": DataTask(
        "underground_structures",
        "restore and validate the PLATEAU UC24-13 Sapporo underground scene",
        "scripts/fetch_plateau_uc24_13.py",
        inputs=("data/plateau/uc24_13_sapporo/source_manifest.json",),
        outputs=("data/plateau/uc24_13_sapporo/manifest.json",),
        manifest="data/plateau/uc24_13_sapporo/manifest.json",
        network=True,
        force_argument=True,
        offline_argument=True,
        check_stale=False,
    ),
    "underground_access_osm": DataTask(
        "underground_access_osm",
        "refresh the bounded OSM access snapshot for the Sapporo underground scene",
        "scripts/fetch_osm_sapporo_underground.py",
        inputs=("data/osm/sapporo_underground_access/query.overpassql",),
        outputs=(
            "data/osm/sapporo_underground_access/features.geojson",
            "data/osm/sapporo_underground_access/metadata.json",
        ),
        network=True,
        automatic=False,
        check_stale=False,
    ),
    "underground_scenes": DataTask(
        "underground_scenes",
        "rebuild renderer-neutral handoffs for the canonical underground scenes",
        "scripts/build_underground_scenes.py",
        inputs=(
            "data/plateau/uc24_16_nihonbashi/manifest.json",
            "data/plateau/uc24_16_nihonbashi/audit_index.json",
            "data/plateau/uc24_13_sapporo/manifest.json",
            "data/osm/sapporo_underground_access/features.geojson",
            "data/osm/sapporo_underground_access/metadata.json",
        ),
        outputs=(
            "data/scenes/underground/catalog.json",
            "data/plateau/uc24_16_nihonbashi/scene_handoff.json",
            "data/plateau/uc24_13_sapporo/scene_handoff.json",
        ),
        automatic=False,
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
            "data/external/gsi_evacuation/yokohama_evacuation.geojson",
            "data/google/satellite_embedding/embedding_evidence.geojson",
        ),
        outputs=(
            "data/yokohama/official_facility_resilience.geojson",
            "data/evidence/yokohama_zones.geojson",
            "data/evidence/mobara_zones.geojson",
            "data/evidence/multiscale_summary.json",
        ),
        dependencies=("bootstrap", "embedding", "gsi_evacuation"),
    ),
    "store": DataTask(
        "store",
        "build the spatially indexed SQLite store from every committed dataset",
        "scripts/build_spatial_store.py",
        inputs=STORE_INPUTS,
        outputs=(STORE_PATH,),
        dependencies=("bootstrap", "joint", "evidence"),
        force_argument=True,
    ),
}


def _existing_outputs(task: DataTask, root: Path) -> tuple[list[Path], list[str]]:
    paths = [root / item for item in task.outputs]
    missing = [item for item, path in zip(task.outputs, paths, strict=True) if not valid_data_file(path)]
    for pattern in task.output_globs:
        matches = [path for path in root.glob(pattern) if path.is_file() and path.stat().st_size > 0]
        paths.extend(matches)
        if not matches:
            missing.append(pattern)
    if task.manifest and valid_data_file(root / task.manifest):
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
            if not valid_data_file(path):
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
    missing_cache = [item for item in task.cache_outputs if not valid_data_file(root / item)]
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
    command = [sys.executable, str(root / task.script)]
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
        missing_cache = [item for item in task.cache_outputs if not valid_data_file(root / item)]
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
            failure = json_file_failure(path)
            if failure:
                failures.append(f"invalid {relative}: {failure}")
    registry_path = root / "data/external/source_registry.json"
    if registry_path.is_file():
        try:
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return failures
        for source in registry.get("sources", []):
            if source.get("status") != "integrated":
                continue
            source_id = source.get("id", "<unknown>")
            if not source.get("retrieved_at"):
                failures.append(f"integrated FL source lacks retrieved_at: {source_id}")
            if "source_updated_at" not in source:
                failures.append(f"integrated FL source lacks source_updated_at: {source_id}")
            elif source["source_updated_at"] is None and not source.get("source_updated_at_note"):
                failures.append(f"integrated FL source has unexplained source_updated_at: {source_id}")
    return failures
