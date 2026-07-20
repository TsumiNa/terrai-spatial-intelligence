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

    def test_demo_exposes_architecture_and_keeps_surface_sl_empty(self) -> None:
        html = read("index.html")
        app = read("app.js")
        self.assertIn('data-module="architecture"', html)
        self.assertIn('id="architecture-board"', html)
        self.assertIn("当前评分是透明 AL 启发式，不是 SL 预测", html)
        self.assertIn('metric("地表 SL 补值", 0', app)
        self.assertIn('params.get("module") : "architecture"', app)

    def test_architecture_language_contract_has_japanese_and_english(self) -> None:
        translations = read("i18n.js")
        source = '"FL → SL → AL 架构"'
        self.assertGreaterEqual(translations.count(source), 2)
        self.assertIn('"FL → SL → AL architecture"', translations)
        self.assertIn('"FL → SL → AL アーキテクチャ"', translations)

    def test_readme_links_decision_and_refactor_history(self) -> None:
        readme = read("README.md")
        for relative in (
            "docs/architecture/FL_SL_AL_CONCEPT.md",
            "docs/adr/0001-fl-sl-al-conceptual-layers.md",
            "docs/refactor/2026-07-fl-sl-al-factor-of-concept.md",
        ):
            self.assertIn(relative, readme)


if __name__ == "__main__":
    unittest.main()

