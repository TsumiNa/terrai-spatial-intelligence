"""Unified CLI for serving, rebuilding and validating the TerrAI demo."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .data_tasks import TASKS, ensure_data, status_rows, validate_json_outputs


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PIPELINES = ("joint", "evidence")

REQUIRED_FILES = [
    "index.html",
    "styles.css",
    "i18n.js",
    "audit.js",
    "app.js",
    "vendor/leaflet.js",
    "vendor/leaflet.css",
    "terrai_spatial/data_tasks.py",
    "scripts/ensure_data.py",
    "scripts/bootstrap_packaged_data.py",
    "data/tiles/manifest.json",
    "data/yokohama/building_risk.geojson",
    "data/yokohama/road_priority.geojson",
    "data/yokohama/official_facility_resilience.geojson",
    "data/mobara/site_cells.geojson",
    "data/mobara/tepco_grid_screen.json",
    "data/joint/joint_summary.json",
    "data/google/satellite_embedding/summary.json",
    "data/evidence/multiscale_summary.json",
]


def command_build(args: argparse.Namespace) -> None:
    selected = list(DEFAULT_PIPELINES) if args.only == "all" else [args.only]
    ensure_data(selected=selected, allow_network=False, force=True)


def command_fetch(args: argparse.Namespace) -> None:
    ensure_data(selected=[args.dataset], allow_network=True, force=True)


def command_data(args: argparse.Namespace) -> None:
    if args.action == "status":
        for state in status_rows():
            print(f"{state.name:10} {state.status:8} {state.reason}")
        return
    ensure_data(
        selected=args.only,
        allow_network=not args.offline,
        force=args.action == "update",
    )


def command_serve(args: argparse.Namespace) -> None:
    if not args.no_ensure_data:
        print("[TerrAI data] checking startup data", flush=True)
        ensure_data(allow_network=not args.offline)
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
    failures: list[str] = validate_json_outputs()
    for state in status_rows():
        if state.status != "ready":
            failures.append(f"data task {state.name}: {state.status}: {state.reason}")
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
    serve.add_argument("--offline", action="store_true", help="repair local derivatives but do not download missing data")
    serve.add_argument("--no-ensure-data", action="store_true", help="skip the automatic startup data check")
    serve.set_defaults(func=command_serve)

    build = subparsers.add_parser("build", help="rebuild redistributable derived data")
    build.add_argument("--only", choices=["all", "grid", *DEFAULT_PIPELINES], default="all")
    build.set_defaults(func=command_build)

    fetch = subparsers.add_parser("fetch", help="refresh remote open-data assets")
    fetch.add_argument("dataset", choices=("tiles", "embedding"))
    fetch.set_defaults(func=command_fetch)

    data = subparsers.add_parser("data", help="inspect, repair or update all data tasks")
    data.add_argument("action", choices=("status", "ensure", "update"), nargs="?", default="ensure")
    data.add_argument("--only", choices=tuple(TASKS), action="append", help="limit work to one or more tasks")
    data.add_argument("--offline", action="store_true", help="do not download missing remote data")
    data.set_defaults(func=command_data)

    validate = subparsers.add_parser("validate", help="validate required assets and JSON/GeoJSON")
    validate.set_defaults(func=command_validate)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        args.func(args)
    except (RuntimeError, subprocess.CalledProcessError) as error:
        print(f"TerrAI data error: {error}", file=sys.stderr)
        raise SystemExit(2) from error
