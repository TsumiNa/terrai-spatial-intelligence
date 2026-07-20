from __future__ import annotations

import unittest
from pathlib import Path

from terrai_spatial.cli import localized_document, multilingual_documents


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def read(relative: str | Path) -> str:
    return (PROJECT_ROOT / relative).read_text(encoding="utf-8")


class ConceptArchitectureTests(unittest.TestCase):
    def test_multilingual_discovery_is_scoped_to_three_docs_directories(self) -> None:
        documents = multilingual_documents()
        self.assertIn(Path("docs/architecture/FL_SL_AL_CONCEPT.md"), documents)
        self.assertIn(Path("docs/data/gsi-dem5a.md"), documents)
        self.assertIn(Path("docs/summary/2026-07-prototype-state.md"), documents)
        self.assertNotIn(Path("README.md"), documents)
        self.assertNotIn(Path("CONTRIBUTING.md"), documents)
        self.assertNotIn(Path("docs/refactor/fl-sl-al-platform/00-overview.md"), documents)

    def test_scoped_documents_have_language_partners_and_navigation(self) -> None:
        for canonical in multilingual_documents():
            siblings = (canonical, localized_document(canonical, "ja"), localized_document(canonical, "en"))
            for sibling in siblings:
                self.assertTrue((PROJECT_ROOT / sibling).is_file(), sibling)
                content = read(sibling)
                for linked in siblings:
                    self.assertIn(f"({linked.name})", content, f"{sibling} -> {linked.name}")

    def test_non_scoped_documentation_is_english_only(self) -> None:
        for relative in (
            "README",
            "CONTRIBUTING",
            "docs/README",
            "docs/refactor/fl-sl-al-platform/00-overview",
            "docs/refactor/fl-sl-al-platform/01-concept-layers-pr1a",
        ):
            self.assertTrue((PROJECT_ROOT / f"{relative}.md").is_file())
            self.assertFalse((PROJECT_ROOT / f"{relative}.ja.md").exists())
            self.assertFalse((PROJECT_ROOT / f"{relative}.en.md").exists())

    def test_canonical_concept_defines_layers_and_non_goals(self) -> None:
        concept = read("docs/architecture/FL_SL_AL_CONCEPT.md")
        for token in (
            "Foundation Data Layer",
            "Synthetic Data Layer",
            "Application Layer",
            "observed、synthetic 与 unresolved",
            "本次明确不做",
        ):
            self.assertIn(token, concept)

    def test_customer_ui_keeps_internal_architecture_out_of_navigation(self) -> None:
        html = read("frontend/index.html")
        self.assertNotIn('data-module="architecture"', html)
        self.assertIn('data-module="overview"', html)
        self.assertIn('data-module="evidence"', html)

    def test_call_sequence_document_remains_trilingual(self) -> None:
        canonical = Path("docs/architecture/FRONTEND_BACKEND.md")
        for relative in (canonical, localized_document(canonical, "ja"), localized_document(canonical, "en")):
            content = read(relative)
            self.assertEqual(content.count("sequenceDiagram"), 3)
            for token in ("GET /bootstrap", "GET /assets/tiles/", "GET /features/solar", "SQLite"):
                self.assertIn(token, content)


if __name__ == "__main__":
    unittest.main()
