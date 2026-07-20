from __future__ import annotations

import argparse
import json
import tempfile
import unittest
from pathlib import Path

from terrai_spatial.cli import (
    REFACTOR_PLAN_PATTERN,
    ROOT,
    command_validate,
    localized_document,
    multilingual_documents,
    validate_json,
)


def read(relative: str | Path) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


class ValidateJsonTests(unittest.TestCase):
    def write(self, directory: str, name: str, text: str) -> Path:
        path = Path(directory) / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_accepts_a_plain_object_and_a_feature_collection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            summary = self.write(directory, "summary.json", json.dumps({"count": 1}))
            collection = self.write(
                directory, "cells.geojson", json.dumps({"type": "FeatureCollection", "features": []})
            )
            self.assertEqual(validate_json(summary), (True, "ok"))
            self.assertEqual(validate_json(collection), (True, "ok"))

    def test_rejects_malformed_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self.write(directory, "summary.json", "{")
            ok, message = validate_json(path)
            self.assertFalse(ok)
            self.assertIn("Expecting", message)

    def test_rejects_geojson_that_is_not_a_feature_collection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self.write(directory, "cells.geojson", json.dumps({"type": "Feature"}))
            self.assertEqual(validate_json(path), (False, "GeoJSON root is not a FeatureCollection"))

    def test_rejects_a_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ok, message = validate_json(Path(directory) / "absent.json")
            self.assertFalse(ok)
            self.assertIn("No such file", message)


class DocumentDiscoveryTests(unittest.TestCase):
    def test_discovery_is_limited_to_multilingual_directories(self) -> None:
        documents = multilingual_documents()
        self.assertIn(Path("docs/architecture/FL_SL_AL_CONCEPT.md"), documents)
        self.assertIn(Path("docs/data/gsi-dem5a/README.md"), documents)
        self.assertIn(Path("docs/summary/2026-07-prototype-state/README.md"), documents)
        self.assertNotIn(Path("README.md"), documents)
        self.assertNotIn(Path("CONTRIBUTING.md"), documents)
        self.assertNotIn(Path("docs/refactor/fl-sl-al-platform/00-overview.md"), documents)
        self.assertFalse([path for path in documents if path.name.endswith((".ja.md", ".zh.md"))])

    def test_localized_document_derives_language_partners(self) -> None:
        canonical = Path("docs/architecture/FL_SL_AL_CONCEPT.md")
        self.assertEqual(
            localized_document(canonical, "ja"), Path("docs/architecture/FL_SL_AL_CONCEPT.ja.md")
        )
        self.assertEqual(
            localized_document(canonical, "zh"), Path("docs/architecture/FL_SL_AL_CONCEPT.zh.md")
        )

    def test_refactor_plan_pattern_accepts_only_numbered_pr_filenames(self) -> None:
        self.assertTrue(REFACTOR_PLAN_PATTERN.fullmatch("01-concept-layers-pr1a.md"))
        self.assertTrue(REFACTOR_PLAN_PATTERN.fullmatch("02-exhibition-fastapi-pr12.md"))
        for name in ("1-concept-pr1.md", "01-Concept-pr1.md", "01-concept-layers.md", "00-overview.md"):
            self.assertIsNone(REFACTOR_PLAN_PATTERN.fullmatch(name), name)


class RepositoryContractTests(unittest.TestCase):
    """Contracts `command_validate` does not itself enforce, plus its success path."""

    def test_validate_accepts_the_current_repository(self) -> None:
        command_validate(argparse.Namespace())

    def test_concept_document_defines_layers_and_development_non_goals(self) -> None:
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
            self.assertIn(token, concept)

    def test_customer_ui_keeps_internal_architecture_out_of_primary_navigation(self) -> None:
        html = read("frontend/index.html")
        app = read("frontend/app.js")
        self.assertNotIn('data-module="architecture"', html)
        self.assertNotIn('id="architecture-board"', html)
        self.assertNotIn("function renderArchitecture()", app)
        self.assertIn('data-module="overview"', html)
        self.assertIn('data-module="evidence"', html)
        self.assertIn("证据与可靠性", html)

    def test_evidence_module_label_is_translated_to_japanese_and_english(self) -> None:
        translations = read("frontend/i18n.js")
        self.assertGreaterEqual(translations.count('"证据与可靠性"'), 2)
        self.assertIn('"Evidence & reliability"', translations)
        self.assertIn('"証拠と信頼性"', translations)

    def test_root_readme_links_current_architecture_data_and_refactor(self) -> None:
        readme = read("README.md")
        for relative in (
            "docs/architecture/FRONTEND_BACKEND.md",
            "docs/architecture/FL_SL_AL_CONCEPT.md",
            "docs/data/README.md",
            "docs/refactor/fl-sl-al-platform/00-overview.md",
        ):
            self.assertIn(relative, readme)

    def test_non_scoped_documentation_is_english_only(self) -> None:
        for relative in (
            "README",
            "CONTRIBUTING",
            "docs/README",
            "docs/refactor/fl-sl-al-platform/00-overview",
        ):
            self.assertTrue((ROOT / f"{relative}.md").is_file())
            self.assertFalse((ROOT / f"{relative}.ja.md").exists())
            self.assertFalse((ROOT / f"{relative}.en.md").exists())
            self.assertFalse((ROOT / f"{relative}.zh.md").exists())

    def test_data_catalog_is_at_root_and_records_use_subfolders(self) -> None:
        expected = {"README.md", "README.ja.md", "README.zh.md"}
        data_root = ROOT / "docs/data"
        self.assertEqual({path.name for path in data_root.glob("*.md")}, expected)
        for folder in (path for path in data_root.iterdir() if path.is_dir()):
            self.assertEqual({path.name for path in folder.glob("*.md")}, expected, folder)

        summary_root = ROOT / "docs/summary"
        self.assertFalse(list(summary_root.glob("*.md")))
        for folder in (path for path in summary_root.iterdir() if path.is_dir()):
            self.assertEqual({path.name for path in folder.glob("*.md")}, expected, folder)

    def test_call_sequence_document_tracks_runtime_in_three_languages(self) -> None:
        canonical = Path("docs/architecture/FRONTEND_BACKEND.md")
        for relative in (canonical, localized_document(canonical, "ja"), localized_document(canonical, "zh")):
            call_structure = read(relative)
            self.assertEqual(call_structure.count("sequenceDiagram"), 3, relative)
            for token in ("GET /bootstrap", "GET /assets/tiles/", "GET /features/solar", "SQLite"):
                self.assertIn(token, call_structure, relative)


if __name__ == "__main__":
    unittest.main()
