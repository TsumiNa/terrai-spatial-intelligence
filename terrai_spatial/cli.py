"""Unified CLI for serving, rebuilding and validating the TerrAI demo."""

from __future__ import annotations

import argparse
import json
import re
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

DOCS_TOP_LEVEL_DIRECTORIES = {"architecture", "refactor", "data", "summary", "others"}
MULTILINGUAL_DOCS_DIRECTORIES = ("architecture", "data", "summary")
REFACTOR_PLAN_PATTERN = re.compile(r"^\d{2}-[a-z0-9-]+-pr\d+[a-z]?\.md$")


def localized_document(path: Path, language: str) -> Path:
    return path.with_suffix(f".{language}.md")


def multilingual_documents() -> list[Path]:
    """Discover canonical English docs only where translations are required."""
    documents: list[Path] = []
    for directory in MULTILINGUAL_DOCS_DIRECTORIES:
        documents.extend(
            path.relative_to(ROOT)
            for path in sorted((ROOT / "docs" / directory).rglob("*.md"))
            if not path.name.endswith((".ja.md", ".zh.md"))
        )
    return documents

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


def data_task_failures() -> list[str]:
    """Report data pipelines that are not ready.

    This reads working-copy file modification times, so a checkout that rewrites
    a pipeline input reports `stale` even though repository content is correct.
    Keep it out of `contract_failures` for that reason.
    """

    return [
        f"data task {state.name}: {state.status}: {state.reason}"
        for state in status_rows()
        if state.status != "ready"
    ]


def contract_failures() -> list[str]:
    """Report every violation that is decided by repository content alone.

    Required assets, JSON validity, documentation structure and language groups,
    and the runtime string contracts. Deterministic for a given checkout.
    """

    failures: list[str] = validate_json_outputs()
    for relative in REQUIRED_FILES:
        path = ROOT / relative
        if not path.is_file():
            failures.append(f"missing: {relative}")

    for path in sorted((ROOT / "data").rglob("*.json")) + sorted((ROOT / "data").rglob("*.geojson")):
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
            "Explicit non-goals",
            "observed, synthetic, and unresolved",
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
        "docs/architecture/FRONTEND_BACKEND.md": (
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

    docs_root = ROOT / "docs"
    actual_directories = {
        path.name for path in docs_root.iterdir() if path.is_dir() and any(path.iterdir())
    }
    if actual_directories != DOCS_TOP_LEVEL_DIRECTORIES:
        failures.append(
            "docs top-level directories must be exactly "
            f"{sorted(DOCS_TOP_LEVEL_DIRECTORIES)}; found {sorted(actual_directories)}"
        )
    allowed_root_docs = {"README.md"}
    loose_docs = {path.name for path in docs_root.glob("*.md")} - allowed_root_docs
    for name in sorted(loose_docs):
        failures.append(f"loose document directly under docs/: {name}")
    if (docs_root / "adr").exists() and any((docs_root / "adr").iterdir()):
        failures.append("docs/adr is prohibited; preserve decisions in the refactor overview")

    documents = multilingual_documents()
    expected_document_paths: set[Path] = set()
    for canonical in documents:
        siblings = (
            canonical.name,
            localized_document(canonical, "ja").name,
            localized_document(canonical, "zh").name,
        )
        group = (canonical, localized_document(canonical, "ja"), localized_document(canonical, "zh"))
        expected_document_paths.update(group)
        for document in group:
            path = ROOT / document
            if not path.is_file():
                failures.append(f"missing trilingual partner: {document}")
                continue
            content = path.read_text(encoding="utf-8")
            if content.count("```") % 2:
                failures.append(f"unclosed code fence: {document}")
            for sibling in siblings:
                if f"({sibling})" not in content:
                    failures.append(f"trilingual navigation missing: {document}: {sibling}")

    discovered_multilingual_markdown = {
        path.relative_to(ROOT)
        for directory in MULTILINGUAL_DOCS_DIRECTORIES
        for path in (docs_root / directory).rglob("*.md")
    }
    for orphan in sorted(discovered_multilingual_markdown - expected_document_paths):
        if orphan.name.endswith((".ja.md", ".zh.md")):
            failures.append(f"localized document has no canonical English partner: {orphan}")

    for path in (ROOT / "README.md", ROOT / "CONTRIBUTING.md", docs_root / "README.md"):
        if not path.is_file():
            failures.append(f"missing English documentation entrypoint: {path.relative_to(ROOT)}")
    for path in docs_root.rglob("*.md"):
        if path.read_text(encoding="utf-8").count("```") % 2:
            failures.append(f"unclosed code fence: {path.relative_to(ROOT)}")

    required_group_files = {"README.md", "README.ja.md", "README.zh.md"}
    for category in ("data", "summary"):
        category_root = docs_root / category
        loose = {path.name for path in category_root.glob("*.md")}
        allowed_loose = required_group_files if category == "data" else set()
        if loose != allowed_loose:
            failures.append(
                f"{category} root Markdown files must be exactly {sorted(allowed_loose)}; "
                f"found {sorted(loose)}"
            )
        for folder in sorted(path for path in category_root.iterdir() if path.is_dir()):
            actual = {path.name for path in folder.glob("*.md")}
            if actual != required_group_files:
                failures.append(
                    f"{category} group {folder.name} must contain exactly "
                    f"{sorted(required_group_files)}; found {sorted(actual)}"
                )

    refactor_root = docs_root / "refactor"
    for refactor_folder in sorted(path for path in refactor_root.iterdir() if path.is_dir()):
        overview = refactor_folder.relative_to(ROOT) / "00-overview.md"
        if not (ROOT / overview).is_file():
            failures.append(f"refactor folder missing 00-overview.md: {refactor_folder.name}")
        for path in refactor_folder.glob("*.md"):
            if path.name == "00-overview.md":
                continue
            if not REFACTOR_PLAN_PATTERN.fullmatch(path.name):
                failures.append(f"invalid refactor plan filename: {path.relative_to(ROOT)}")

    data_headings = {
        "en": (
            "## Data description",
            "## Source",
            "## Use in this project",
            "## License",
            "## Commercial-use cautions",
        ),
        "zh": ("## 数据内容", "## 来源", "## 在本项目中的使用", "## License", "## 商业使用注意"),
        "ja": ("## データの内容", "## 出典", "## 本 project での利用", "## License", "## 商用利用時の注意"),
    }
    for canonical in sorted((docs_root / "data").glob("*/README.md")):
        relative = canonical.relative_to(ROOT)
        for language, document in (
            ("en", relative),
            ("ja", localized_document(relative, "ja")),
            ("zh", localized_document(relative, "zh")),
        ):
            path = ROOT / document
            if not path.is_file():
                continue
            content = path.read_text(encoding="utf-8")
            for heading in data_headings[language]:
                if heading not in content:
                    failures.append(f"data card missing section: {document}: {heading}")
    client_html = (ROOT / "frontend/index.html").read_text(encoding="utf-8")
    if 'data-module="architecture"' in client_html:
        failures.append("internal architecture module leaked into the customer navigation")
    return failures


def command_validate(_: argparse.Namespace) -> None:
    failures = contract_failures() + data_task_failures()
    if failures:
        print("TerrAI validation failed:")
        for failure in failures:
            print(f"  - {failure}")
        raise SystemExit(1)

    # Counted only once validation has passed, and without materialising the
    # paths: these numbers exist for the success message alone.
    json_count = sum(1 for _ in (ROOT / "data").rglob("*.json")) + sum(
        1 for _ in (ROOT / "data").rglob("*.geojson")
    )
    print(
        "TerrAI validation passed: "
        f"{len(REQUIRED_FILES)} required assets, {json_count} JSON/GeoJSON files, "
        f"{len(multilingual_documents())} scoped trilingual document groups"
    )


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
