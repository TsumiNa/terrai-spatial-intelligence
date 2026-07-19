"""Unified CLI for serving, rebuilding and validating the TerrAI demo."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

PIPELINES = {
    "grid": SCRIPTS / "parse_tepco_grid.py",
    "joint": SCRIPTS / "build_joint_analysis.py",
    "evidence": SCRIPTS / "build_multiscale_evidence.py",
}

DEFAULT_PIPELINES = ("joint", "evidence")

REMOTE_TASKS = {
    "tiles": SCRIPTS / "fetch_visual_tiles.py",
    "embedding": SCRIPTS / "fetch_google_satellite_embedding.py",
}

REQUIRED_FILES = [
    "index.html",
    "styles.css",
    "i18n.js",
    "audit.js",
    "app.js",
    "vendor/leaflet.js",
    "vendor/leaflet.css",
    "data/yokohama/building_risk.geojson",
    "data/yokohama/road_priority.geojson",
    "data/yokohama/official_facility_resilience.geojson",
    "data/mobara/site_cells.geojson",
    "data/mobara/tepco_grid_screen.json",
    "data/joint/joint_summary.json",
    "data/google/satellite_embedding/summary.json",
    "data/evidence/multiscale_summary.json",
]


def run_script(path: Path, extra_args: list[str] | None = None) -> None:
    command = [sys.executable, str(path), *(extra_args or [])]
    subprocess.run(command, cwd=ROOT, check=True)


def command_build(args: argparse.Namespace) -> None:
    selected = list(DEFAULT_PIPELINES) if args.only == "all" else [args.only]
    if "grid" in selected:
        required = [
            ROOT / "data/external/tepco/csv_yosochoryu_chiba_soudensen.csv",
            ROOT / "data/external/tepco/csv_yosochoryu_chiba_hendensyo.csv",
        ]
        missing = [path.relative_to(ROOT) for path in required if not path.is_file()]
        if missing:
            names = ", ".join(map(str, missing))
            raise SystemExit(
                "TEPCO source files are local-only and missing: "
                f"{names}. See data/external/tepco/README.md."
            )
    for name in selected:
        print(f"[TerrAI] running {name} pipeline", flush=True)
        run_script(PIPELINES[name])


def command_fetch(args: argparse.Namespace) -> None:
    run_script(REMOTE_TASKS[args.dataset], args.extra)


def command_serve(args: argparse.Namespace) -> None:
    handler = partial(SimpleHTTPRequestHandler, directory=ROOT)
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"TerrAI demo: http://{args.host}:{args.port}/", flush=True)
    print("Press Ctrl+C to stop.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def validate_json(path: Path) -> tuple[bool, str]:
    try:
        with path.open(encoding="utf-8") as handle:
            value = json.load(handle)
    except (OSError, json.JSONDecodeError) as error:
        return False, str(error)
    if path.suffix == ".geojson" and value.get("type") != "FeatureCollection":
        return False, "GeoJSON root is not a FeatureCollection"
    return True, "ok"


def command_validate(_: argparse.Namespace) -> None:
    failures: list[str] = []
    for relative in REQUIRED_FILES:
        path = ROOT / relative
        if not path.is_file():
            failures.append(f"missing: {relative}")

    json_count = 0
    for path in sorted((ROOT / "data").rglob("*.json")) + sorted((ROOT / "data").rglob("*.geojson")):
        json_count += 1
        ok, message = validate_json(path)
        if not ok:
            failures.append(f"invalid {path.relative_to(ROOT)}: {message}")

    runtime_files = [ROOT / "index.html", ROOT / "app.js", ROOT / "audit.js", ROOT / "styles.css"]
    forbidden = ("dynamic_world", "fetch_dynamic_world", "Dynamic World ·")
    for path in runtime_files:
        content = path.read_text(encoding="utf-8")
        for token in forbidden:
            if token in content:
                failures.append(f"removed runtime dependency still referenced: {path.name}: {token}")

    if failures:
        print("TerrAI validation failed:")
        for failure in failures:
            print(f"  - {failure}")
        raise SystemExit(1)
    print(f"TerrAI validation passed: {len(REQUIRED_FILES)} required assets, {json_count} JSON/GeoJSON files")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="terrai", description="TerrAI Spatial Intelligence demo tools")
    subparsers = parser.add_subparsers(dest="command", required=True)

    serve = subparsers.add_parser("serve", help="serve the static demo locally")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=4176)
    serve.set_defaults(func=command_serve)

    build = subparsers.add_parser("build", help="rebuild redistributable derived data")
    build.add_argument("--only", choices=["all", *PIPELINES], default="all")
    build.set_defaults(func=command_build)

    fetch = subparsers.add_parser("fetch", help="refresh remote open-data assets")
    fetch.add_argument("dataset", choices=sorted(REMOTE_TASKS))
    fetch.add_argument("extra", nargs=argparse.REMAINDER, help="arguments passed to the source adapter")
    fetch.set_defaults(func=command_fetch)

    validate = subparsers.add_parser("validate", help="validate required assets and JSON/GeoJSON")
    validate.set_defaults(func=command_validate)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)
