from __future__ import annotations

import re
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCS_CATEGORIES = {"architecture", "refactor", "data", "summary", "others"}
PLAN_PATTERN = re.compile(r"^\d{2}-[a-z0-9-]+-pr\d+[a-z]?\.md$")


def read(relative: str | Path) -> str:
    return (PROJECT_ROOT / relative).read_text(encoding="utf-8")


def localized(path: Path, language: str) -> Path:
    return path.with_suffix(f".{language}.md")


def canonical_documents() -> list[Path]:
    documents = [Path("README.md"), Path("CONTRIBUTING.md")]
    documents.extend(
        path.relative_to(PROJECT_ROOT)
        for path in sorted((PROJECT_ROOT / "docs").rglob("*.md"))
        if not path.name.endswith((".ja.md", ".en.md"))
    )
    return documents


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

    def test_root_readme_links_current_architecture_data_and_refactor(self) -> None:
        readme = read("README.md")
        for relative in (
            "docs/architecture/FRONTEND_BACKEND.md",
            "docs/architecture/FL_SL_AL_CONCEPT.md",
            "docs/data/README.md",
            "docs/refactor/fl-sl-al-platform/00-overview.md",
        ):
            self.assertIn(relative, readme)

    def test_frontend_backend_call_document_tracks_runtime(self) -> None:
        for relative in (
            "docs/architecture/FRONTEND_BACKEND.md",
            "docs/architecture/FRONTEND_BACKEND.ja.md",
            "docs/architecture/FRONTEND_BACKEND.en.md",
        ):
            call_structure = read(relative)
            self.assertEqual(call_structure.count("sequenceDiagram"), 3)
            for token in ("GET /bootstrap", "GET /assets/tiles/", "GET /features/solar", "SQLite"):
                self.assertIn(token, call_structure)

    def test_docs_have_only_fixed_categories_and_index_at_root(self) -> None:
        docs = PROJECT_ROOT / "docs"
        self.assertEqual(
            {path.name for path in docs.iterdir() if path.is_dir() and any(path.iterdir())},
            DOCS_CATEGORIES,
        )
        self.assertEqual(
            {path.name for path in docs.glob("*.md")},
            {"README.md", "README.ja.md", "README.en.md"},
        )
        self.assertFalse((docs / "adr").exists() and any((docs / "adr").iterdir()))

    def test_all_documentation_is_discovered_as_trilingual_groups(self) -> None:
        for canonical in canonical_documents():
            siblings = (canonical, localized(canonical, "ja"), localized(canonical, "en"))
            for sibling in siblings:
                self.assertTrue((PROJECT_ROOT / sibling).is_file(), sibling)
                content = read(sibling)
                self.assertEqual(content.count("```") % 2, 0, f"unclosed code fence: {sibling}")
                for linked in siblings:
                    self.assertIn(f"({linked.name})", content, f"{sibling} -> {linked.name}")

    def test_refactor_folders_have_overview_and_named_pr_plans(self) -> None:
        for folder in (PROJECT_ROOT / "docs/refactor").iterdir():
            if not folder.is_dir():
                continue
            self.assertTrue((folder / "00-overview.md").is_file())
            for path in folder.glob("*.md"):
                if path.name == "00-overview.md" or path.name.endswith((".ja.md", ".en.md")):
                    continue
                self.assertRegex(path.name, PLAN_PATTERN)

    def test_each_integrated_data_card_has_required_sections(self) -> None:
        headings = ("## 来源", "## 在本项目中的使用", "## License", "## 商业使用注意")
        for path in (PROJECT_ROOT / "docs/data").glob("*.md"):
            if path.name == "README.md" or path.name.endswith((".ja.md", ".en.md")):
                continue
            content = path.read_text(encoding="utf-8")
            for heading in headings:
                self.assertIn(heading, content, f"{path.name}: {heading}")


if __name__ == "__main__":
    unittest.main()
