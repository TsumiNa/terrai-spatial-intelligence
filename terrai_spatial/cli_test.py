from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from terrai_spatial.data_tasks import TASKS
from terrai_spatial.cli import (
    REFACTOR_PLAN_PATTERN,
    REFACTOR_STATES_NEEDING_REASON,
    ROOT,
    contract_failures,
    build_parser,
    localized_document,
    multilingual_documents,
    refactor_status_failures,
    validate_json,
)


LANGUAGE_GROUP = {"README.md", "README.ja.md", "README.zh.md"}


def read(relative: str | Path) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def write(directory: Path, name: str, text: str) -> Path:
    path = directory / name
    path.write_text(text, encoding="utf-8")
    return path


# --- validate_json -----------------------------------------------------------


def test_validate_json_accepts_a_plain_object_and_a_feature_collection(tmp_path: Path) -> None:
    summary = write(tmp_path, "summary.json", json.dumps({"count": 1}))
    collection = write(
        tmp_path, "cells.geojson", json.dumps({"type": "FeatureCollection", "features": []})
    )
    assert validate_json(summary) == (True, "ok")
    assert validate_json(collection) == (True, "ok")


def test_validate_json_rejects_malformed_json(tmp_path: Path) -> None:
    ok, message = validate_json(write(tmp_path, "summary.json", "{"))
    assert not ok
    assert "Expecting" in message


def test_validate_json_rejects_geojson_that_is_not_a_feature_collection(tmp_path: Path) -> None:
    path = write(tmp_path, "cells.geojson", json.dumps({"type": "Feature"}))
    assert validate_json(path) == (False, "GeoJSON root is not a FeatureCollection")


def test_validate_json_rejects_a_missing_file(tmp_path: Path) -> None:
    ok, message = validate_json(tmp_path / "absent.json")
    assert not ok
    assert "No such file" in message


# --- document discovery ------------------------------------------------------


def test_discovery_is_limited_to_multilingual_directories() -> None:
    documents = multilingual_documents()
    assert Path("docs/architecture/FL_SL_AL_CONCEPT.md") in documents
    assert Path("docs/data/gsi-dem5a/README.md") in documents
    assert Path("docs/summary/2026-07-prototype-state/README.md") in documents
    assert Path("README.md") not in documents
    assert Path("CONTRIBUTING.md") not in documents
    assert Path("docs/refactor/fl-sl-al-platform/00-overview.md") not in documents
    assert not [path for path in documents if path.name.endswith((".ja.md", ".zh.md"))]


@pytest.mark.parametrize("language", ["ja", "zh"])
def test_localized_document_derives_language_partners(language: str) -> None:
    canonical = Path("docs/architecture/FL_SL_AL_CONCEPT.md")
    assert localized_document(canonical, language) == Path(
        f"docs/architecture/FL_SL_AL_CONCEPT.{language}.md"
    )


@pytest.mark.parametrize("name", ["01-concept-layers-pr1a.md", "02-exhibition-fastapi-pr12.md"])
def test_refactor_plan_pattern_accepts_numbered_pr_filenames(name: str) -> None:
    assert REFACTOR_PLAN_PATTERN.fullmatch(name)


@pytest.mark.parametrize(
    "name", ["1-concept-pr1.md", "01-Concept-pr1.md", "01-concept-layers.md", "00-overview.md"]
)
def test_refactor_plan_pattern_rejects_other_filenames(name: str) -> None:
    assert REFACTOR_PLAN_PATTERN.fullmatch(name) is None


# --- repository contracts ----------------------------------------------------
# Contracts `command_validate` does not itself enforce, plus its success path.


def test_repository_content_satisfies_every_contract() -> None:
    """Content only. Data-pipeline readiness is mtime-derived and belongs to the CLI, not here."""
    assert contract_failures() == []


def test_concept_document_defines_layers_and_development_non_goals() -> None:
    concept = read("docs/architecture/FL_SL_AL_CONCEPT.md")
    for token in (
        "Foundation Data Layer",
        "Synthetic Data Layer",
        "Application Layer",
        "observed, synthetic, and unresolved",
        "Explicit non-goals",
        "schema",
        "API",
    ):
        assert token in concept


def test_customer_ui_keeps_internal_architecture_out_of_primary_navigation() -> None:
    registry = read("webapp/src/lib/modules.ts")
    assert '"architecture"' not in registry
    assert '"overview"' in registry
    assert '"evidence"' in registry


def test_evidence_module_label_is_translated_to_japanese_and_english() -> None:
    catalogs = read("webapp/src/lib/i18n/messages.ts")
    assert '"nav.evidence": "证据与可靠性"' in catalogs
    assert '"nav.evidence": "証拠と信頼性"' in catalogs
    assert '"nav.evidence": "Evidence & reliability"' in catalogs


@pytest.mark.parametrize(
    "relative",
    [
        "docs/architecture/FRONTEND_BACKEND.md",
        "docs/architecture/FL_SL_AL_CONCEPT.md",
        "docs/data/README.md",
        "docs/refactor/fl-sl-al-platform/00-overview.md",
    ],
)
def test_root_readme_links_current_architecture_data_and_refactor(relative: str) -> None:
    assert relative in read("README.md")


@pytest.mark.parametrize(
    "relative", ["README", "CONTRIBUTING", "docs/README", "docs/refactor/fl-sl-al-platform/00-overview"]
)
def test_non_scoped_documentation_is_english_only(relative: str) -> None:
    assert (ROOT / f"{relative}.md").is_file()
    for suffix in (".ja.md", ".en.md", ".zh.md"):
        assert not (ROOT / f"{relative}{suffix}").exists()


def test_data_catalog_is_at_root_and_records_use_subfolders() -> None:
    data_root = ROOT / "docs/data"
    assert {path.name for path in data_root.glob("*.md")} == LANGUAGE_GROUP
    for folder in (path for path in data_root.iterdir() if path.is_dir()):
        assert {path.name for path in folder.glob("*.md")} == LANGUAGE_GROUP, folder


def test_summary_groups_live_in_subfolders() -> None:
    summary_root = ROOT / "docs/summary"
    assert not list(summary_root.glob("*.md"))
    for folder in (path for path in summary_root.iterdir() if path.is_dir()):
        assert {path.name for path in folder.glob("*.md")} == LANGUAGE_GROUP, folder


@pytest.mark.parametrize("language", [None, "ja", "zh"])
def test_call_sequence_document_tracks_runtime_in_three_languages(language: str | None) -> None:
    canonical = Path("docs/architecture/FRONTEND_BACKEND.md")
    relative = canonical if language is None else localized_document(canonical, language)
    call_structure = read(relative)
    assert call_structure.count("sequenceDiagram") == 3
    for token in ("GET /bootstrap", "GET /assets/tiles/", "GET /features/solar", "SQLite"):
        assert token in call_structure


# --- refactor plan status -----------------------------------------------------
# Without a machine-readable status, progress across a multi-stage refactor can
# only be learned by opening every file and comparing it against reality.


def plan(directory: Path, status: str) -> Path:
    return write(directory, "01-topic-pr1.md", f"# Title\n\n- Status: {status}\n")


@pytest.mark.parametrize("state", ["Planned", "In progress", "Completed"])
def test_refactor_status_accepts_a_self_sufficient_state(tmp_path: Path, state: str) -> None:
    assert refactor_status_failures(plan(tmp_path, state)) == []


@pytest.mark.parametrize(
    "status",
    [
        "Blocked — no subsurface dataset is integrated",
        "Superseded by docs/refactor/maplibre-migration/",
        "Planned — direction only, no PR stages written yet",
    ],
)
def test_refactor_status_accepts_a_qualifier_after_the_state(tmp_path: Path, status: str) -> None:
    assert refactor_status_failures(plan(tmp_path, status)) == []


@pytest.mark.parametrize("state", REFACTOR_STATES_NEEDING_REASON)
def test_refactor_status_rejects_a_stuck_state_without_a_reason(tmp_path: Path, state: str) -> None:
    # "Blocked" alone says something is stuck without saying on what.
    failures = refactor_status_failures(plan(tmp_path, state))
    assert "must be followed by a reason" in failures[0]
    assert refactor_status_failures(plan(tmp_path, f"{state} —")) == failures


@pytest.mark.parametrize("status", ["Completed-ish", "In progressss", "Plannedish", "mostly done"])
def test_refactor_status_rejects_near_misses_and_free_text(tmp_path: Path, status: str) -> None:
    assert "must be one of" in refactor_status_failures(plan(tmp_path, status))[0]


def test_refactor_status_rejects_a_missing_line(tmp_path: Path) -> None:
    path = write(tmp_path, "01-topic-pr1.md", "# Title\n\n- Refactor: something\n")
    assert "missing a status line" in refactor_status_failures(path)[0]


def test_every_refactor_document_declares_a_known_state() -> None:
    documents = sorted((ROOT / "docs/refactor").rglob("*.md"))
    assert documents
    for path in documents:
        if path.name.endswith((".ja.md", ".zh.md")):
            continue
        assert refactor_status_failures(path) == [], path
# --- fetch targets ------------------------------------------------------------


def fetch_choices() -> set[str]:
    """Read the fetch task choices, locating the actions by role not by position."""

    parser = build_parser()
    subparsers = next(
        action for action in parser._actions if isinstance(action, argparse._SubParsersAction)
    )
    task = next(action for action in subparsers.choices["fetch"]._actions if action.dest == "task")
    return set(task.choices)


def fetch_accepts(name: str) -> bool:
    """Behavioural check, touching no argparse internals at all."""

    try:
        build_parser().parse_args(["fetch", name])
    except SystemExit:
        return False
    return True


def test_fetch_offers_every_task_that_downloads() -> None:
    """Derived, not listed: gsi_evacuation and mlit were missing while it was hand-written."""
    expected = {name for name, task in TASKS.items() if task.network or task.repair_missing_cache}
    assert fetch_choices() == expected


def test_fetch_uses_task_names_so_one_vocabulary_spans_the_cli() -> None:
    # `fetch tepco` used to alias the `grid` task, while `data --only` wanted `grid`.
    assert fetch_choices() <= set(TASKS)
    assert "tepco" not in fetch_choices()


def test_fetch_includes_grid_even_though_it_declares_no_network() -> None:
    assert TASKS["grid"].network is False
    assert "grid" in fetch_choices()


def test_fetch_parses_every_downloading_task_and_rejects_others() -> None:
    for name, task in TASKS.items():
        downloads = task.network or task.repair_missing_cache
        assert fetch_accepts(name) is downloads, name
    assert not fetch_accepts("tepco")
    assert not fetch_accepts("no-such-task")


# --- validate --skip-data-tasks -----------------------------------------------
# A fresh clone stamps every file with the checkout time, so data-task freshness
# is undecidable there. CI needs to check repository content without it.


def test_validate_skipping_data_tasks_still_checks_repository_content() -> None:
    parser = build_parser()
    assert parser.parse_args(["validate", "--skip-data-tasks"]).skip_data_tasks is True
    assert parser.parse_args(["validate"]).skip_data_tasks is False


def test_skipping_data_tasks_does_not_weaken_the_content_contracts() -> None:
    # The flag must drop only the working-copy check, never a contract.
    assert contract_failures() == []
