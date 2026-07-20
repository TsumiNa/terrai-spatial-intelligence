from __future__ import annotations

import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (PROJECT_ROOT / relative).read_text(encoding="utf-8")


class ConceptArchitectureTests(unittest.TestCase):
    def test_canonical_document_defines_layers_and_development_non_goals(self) -> None:
        concept = read("docs/architecture/FL_SL_AL_CONCEPT.md")
        for token in (
            "Foundation Data Layer",
            "Synthetic Data Layer",
            "Application Layer",
            "observed、synthetic 与 unresolved",
            "本次明确不做",
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

    def test_architecture_language_contract_has_japanese_and_english(self) -> None:
        translations = read("frontend/i18n.js")
        source = '"证据与可靠性"'
        self.assertGreaterEqual(translations.count(source), 2)
        self.assertIn('"Evidence & reliability"', translations)
        self.assertIn('"証拠と信頼性"', translations)

    def test_readme_links_decision_and_refactor_history(self) -> None:
        readme = read("README.md")
        for relative in (
            "architecture/README.md",
            "docs/architecture/FL_SL_AL_CONCEPT.md",
            "docs/adr/0001-fl-sl-al-conceptual-layers.md",
            "docs/refactor/2026-07-fl-sl-al-factor-of-concept.md",
        ):
            self.assertIn(relative, readme)

    def test_frontend_backend_call_document_tracks_runtime(self) -> None:
        call_structure = read("architecture/README.md")
        self.assertEqual(call_structure.count("sequenceDiagram"), 3)
        for token in (
            "GET /bootstrap",
            "GET /assets/tiles/",
            "GET /features/solar",
            "当前不会再次请求 API",
            "SQLite",
        ):
            self.assertIn(token, call_structure)


if __name__ == "__main__":
    unittest.main()
