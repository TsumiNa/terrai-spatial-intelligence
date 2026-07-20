from __future__ import annotations

import json
from pathlib import Path

import pytest

from terrai_spatial.cli import (
    REFACTOR_PLAN_PATTERN,
    ROOT,
    contract_failures,
    localized_document,
    multilingual_documents,
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
    html = read("frontend/index.html")
    app = read("frontend/app.js")
    assert 'data-module="architecture"' not in html
    assert 'id="architecture-board"' not in html
    assert "function renderArchitecture()" not in app
    assert 'data-module="overview"' in html
    assert 'data-module="evidence"' in html
    assert "证据与可靠性" in html


def test_evidence_module_label_is_translated_to_japanese_and_english() -> None:
    translations = read("frontend/i18n.js")
    assert translations.count('"证据与可靠性"') >= 2
    assert '"Evidence & reliability"' in translations
    assert '"証拠と信頼性"' in translations


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
