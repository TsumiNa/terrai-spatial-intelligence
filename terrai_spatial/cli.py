"""Unified CLI for serving, rebuilding and validating the TerrAI demo."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .data_tasks import TASKS, ensure_data, status_rows, validate_json_outputs


ROOT = Path(__file__).resolve().parents[1]
FRONTEND_ROOT = ROOT / "frontend"
DEFAULT_PIPELINES = ("joint", "evidence")

TRILINGUAL_DOCUMENTS = (
    "README.md",
    "DATA_SOURCES.md",
    "REFACTOR_DECISIONS.md",
    "REMOTE_SENSING_PLAN.md",
    "architecture/README.md",
    "data/external/tepco/README.md",
    "docs/adr/0001-fl-sl-al-conceptual-layers.md",
    "docs/architecture/FL_SL_AL_CONCEPT.md",
    "docs/architecture/FRONTEND_BACKEND_SPLIT.md",
    "docs/refactor/2026-07-fl-sl-al-factor-of-concept.md",
)


def localized_document(relative: str, language: str) -> str:
    path = Path(relative)
    return str(path.with_suffix(f".{language}.md"))

REQUIRED_FILES = [
    "frontend/index.html",
    "frontend/styles.css",
    "frontend/i18n.js",
    "frontend/audit.js",
    "frontend/app.js",
    "terrai_spatial/api.py",
    "terrai_spatial/data_service.py",
    "frontend/vendor/leaflet.js",
    "frontend/vendor/leaflet.css",
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
] + list(TRILINGUAL_DOCUMENTS) + [
    localized_document(relative, language)
    for relative in TRILINGUAL_DOCUMENTS
    for language in ("ja", "en")
]


def command_build(args: argparse.Namespace) -> None:
    selected = list(DEFAULT_PIPELINES) if args.only == "all" else [args.only]
    ensure_data(selected=selected, allow_network=args.only == "grid", force=True)


def command_fetch(args: argparse.Namespace) -> None:
    task = "grid" if args.dataset == "tepco" else args.dataset
    ensure_data(selected=[task], allow_network=True, force=True)


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
    import uvicorn

    config = uvicorn.Config(
        "terrai_spatial.api:app",
        host=args.api_host,
        port=args.api_port,
        log_level="warning",
    )
    api_server = uvicorn.Server(config)
    api_thread = threading.Thread(target=api_server.run, name="terrai-api", daemon=True)
    api_thread.start()
    deadline = time.monotonic() + 10
    while not api_server.started and api_thread.is_alive() and time.monotonic() < deadline:
        time.sleep(0.05)
    if not api_server.started:
        raise SystemExit(f"TerrAI API failed to start on http://{args.api_host}:{args.api_port}")

    handler = partial(SimpleHTTPRequestHandler, directory=FRONTEND_ROOT)
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"TerrAI frontend: http://{args.host}:{args.port}/", flush=True)
    print(f"TerrAI API:      http://{args.api_host}:{args.api_port}/docs", flush=True)
    print("Press Ctrl+C to stop.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        api_server.should_exit = True
        api_thread.join(timeout=5)


def command_api(args: argparse.Namespace) -> None:
    if not args.no_ensure_data:
        ensure_data(allow_network=not args.offline)
    import uvicorn

    uvicorn.run("terrai_spatial.api:app", host=args.host, port=args.port, log_level="info")


def command_frontend(args: argparse.Namespace) -> None:
    handler = partial(SimpleHTTPRequestHandler, directory=FRONTEND_ROOT)
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"TerrAI frontend: http://{args.host}:{args.port}/", flush=True)
    print("Requires the API on http://127.0.0.1:8000 by default. Press Ctrl+C to stop.", flush=True)
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

    runtime_files = [
        ROOT / "frontend/index.html",
        ROOT / "frontend/app.js",
        ROOT / "frontend/audit.js",
        ROOT / "frontend/styles.css",
    ]
    forbidden = ("dynamic_world", "fetch_dynamic_world", "Dynamic World ·")
    for path in runtime_files:
        content = path.read_text(encoding="utf-8")
        for token in forbidden:
            if token in content:
                failures.append(f"removed runtime dependency still referenced: {path.name}: {token}")

    concept_contract = {
        "docs/architecture/FL_SL_AL_CONCEPT.md": (
            "Foundation Data Layer",
            "Synthetic Data Layer",
            "Application Layer",
            "本次明确不做",
            "observed、synthetic 与 unresolved",
        ),
    }
    for relative, required_tokens in concept_contract.items():
        path = ROOT / relative
        if not path.is_file():
            continue
        content = path.read_text(encoding="utf-8")
        for token in required_tokens:
            if token not in content:
                failures.append(f"concept contract missing: {relative}: {token}")

    exhibition_contract = {
        "frontend/index.html": (
            'data-module="overview"',
            'data-module="evidence"',
            "证据与可靠性",
            "点击任意虚线数值查看来源、公式与限制",
        ),
        "frontend/app.js": (
            'fetchJson(`${API_BASE}/bootstrap`)',
            "state.data.recommendations.slope.features",
            "state.data.facilitySummary",
        ),
        "terrai_spatial/api.py": (
            '/api/v1/health',
            '/api/v1/bootstrap',
            '/api/v1/features/{key}',
            '/api/v1/recommendations/{analysis}',
        ),
        "architecture/README.md": (
            "sequenceDiagram",
            "GET /bootstrap",
            "GET /assets/tiles/",
            "GET /features/solar",
        ),
    }
    for relative, required_tokens in exhibition_contract.items():
        content = (ROOT / relative).read_text(encoding="utf-8")
        for token in required_tokens:
            if token not in content:
                failures.append(f"exhibition contract missing: {relative}: {token}")

    for relative in TRILINGUAL_DOCUMENTS:
        canonical = Path(relative)
        siblings = (
            canonical.name,
            canonical.with_suffix(".ja.md").name,
            canonical.with_suffix(".en.md").name,
        )
        for document in (canonical, canonical.with_suffix(".ja.md"), canonical.with_suffix(".en.md")):
            path = ROOT / document
            if not path.is_file():
                continue
            content = path.read_text(encoding="utf-8")
            for sibling in siblings:
                if f"({sibling})" not in content:
                    failures.append(f"trilingual navigation missing: {document}: {sibling}")
    client_html = (ROOT / "frontend/index.html").read_text(encoding="utf-8")
    if 'data-module="architecture"' in client_html:
        failures.append("internal architecture module leaked into the customer navigation")

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
    serve.add_argument("--api-host", default="127.0.0.1")
    serve.add_argument("--api-port", type=int, default=8000)
    serve.add_argument("--offline", action="store_true", help="repair local derivatives but do not download missing data")
    serve.add_argument("--no-ensure-data", action="store_true", help="skip the automatic startup data check")
    serve.set_defaults(func=command_serve)

    api = subparsers.add_parser("api", help="run the FastAPI data and analysis service")
    api.add_argument("--host", default="127.0.0.1")
    api.add_argument("--port", type=int, default=8000)
    api.add_argument("--offline", action="store_true", help="repair local derivatives but do not download data")
    api.add_argument("--no-ensure-data", action="store_true", help="skip the automatic startup data check")
    api.set_defaults(func=command_api)

    frontend = subparsers.add_parser("frontend", help="serve only the static exhibition frontend")
    frontend.add_argument("--host", default="127.0.0.1")
    frontend.add_argument("--port", type=int, default=4176)
    frontend.set_defaults(func=command_frontend)

    build = subparsers.add_parser("build", help="rebuild redistributable derived data")
    build.add_argument("--only", choices=["all", "grid", *DEFAULT_PIPELINES], default="all")
    build.set_defaults(func=command_build)

    fetch = subparsers.add_parser("fetch", help="refresh remote data assets")
    fetch.add_argument("dataset", choices=("tiles", "embedding", "tepco"))
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
