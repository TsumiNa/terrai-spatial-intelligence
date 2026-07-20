from __future__ import annotations

import unittest
from pathlib import Path

from terrai_spatial.cli import localized_document, multilingual_documents


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def read(relative: str | Path) -> str:
    return (PROJECT_ROOT / relative).read_text(encoding="utf-8")


class ConceptArchitectureTests(unittest.TestCase):
    def test_english_is_the_default_multilingual_document(self) -> None:
        concept = read("docs/architecture/FL_SL_AL_CONCEPT.md")
        self.assertIn("# TerrAI FL → SL → AL Conceptual Architecture", concept)
        self.assertIn("observed, synthetic, and unresolved", concept)
        self.assertNotIn("本次明确不做", concept)

    def test_multilingual_discovery_is_scoped_and_uses_zh_partner(self) -> None:
        documents = multilingual_documents()
        self.assertIn(Path("docs/architecture/FL_SL_AL_CONCEPT.md"), documents)
        self.assertIn(Path("docs/data/gsi-dem5a/README.md"), documents)
        self.assertIn(Path("docs/summary/2026-07-prototype-state/README.md"), documents)
        self.assertNotIn(Path("docs/refactor/fl-sl-al-platform/00-overview.md"), documents)
        for canonical in documents:
            for sibling in (
                canonical,
                localized_document(canonical, "ja"),
                localized_document(canonical, "zh"),
            ):
                self.assertTrue((PROJECT_ROOT / sibling).is_file(), sibling)

    def test_data_and_summary_groups_each_have_their_own_subfolder(self) -> None:
        expected = {"README.md", "README.ja.md", "README.zh.md"}
        for category in ("data", "summary"):
            root = PROJECT_ROOT / "docs" / category
            self.assertFalse(list(root.glob("*.md")))
            for folder in (path for path in root.iterdir() if path.is_dir()):
                self.assertEqual({path.name for path in folder.glob("*.md")}, expected, folder)

    def test_non_scoped_documentation_is_english_only(self) -> None:
        for relative in (
            "README",
            "CONTRIBUTING",
            "docs/README",
            "docs/refactor/fl-sl-al-platform/00-overview",
        ):
            self.assertTrue((PROJECT_ROOT / f"{relative}.md").is_file())
            self.assertFalse((PROJECT_ROOT / f"{relative}.ja.md").exists())
            self.assertFalse((PROJECT_ROOT / f"{relative}.zh.md").exists())

    def test_root_readme_links_default_english_documents(self) -> None:
        readme = read("README.md")
        for target in (
            "docs/architecture/FRONTEND_BACKEND.md",
            "docs/architecture/FL_SL_AL_CONCEPT.md",
            "docs/data/catalog/README.md",
            "docs/summary/2026-07-prototype-state/README.md",
        ):
            self.assertIn(target, readme)

    def test_call_sequence_document_remains_trilingual(self) -> None:
        canonical = Path("docs/architecture/FRONTEND_BACKEND.md")
        for relative in (
            canonical,
            localized_document(canonical, "ja"),
            localized_document(canonical, "zh"),
        ):
            content = read(relative)
            self.assertEqual(content.count("sequenceDiagram"), 3)
            self.assertIn("GET /bootstrap", content)


if __name__ == "__main__":
    unittest.main()
