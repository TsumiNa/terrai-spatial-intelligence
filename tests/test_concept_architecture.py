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

    def test_multilingual_discovery_uses_english_japanese_and_chinese(self) -> None:
        documents = multilingual_documents()
        self.assertIn(Path("docs/data/README.md"), documents)
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

    def test_data_catalog_is_at_root_and_records_use_subfolders(self) -> None:
        expected = {"README.md", "README.ja.md", "README.zh.md"}
        data_root = PROJECT_ROOT / "docs/data"
        self.assertEqual({path.name for path in data_root.glob("*.md")}, expected)
        for folder in (path for path in data_root.iterdir() if path.is_dir()):
            self.assertEqual({path.name for path in folder.glob("*.md")}, expected, folder)

        summary_root = PROJECT_ROOT / "docs/summary"
        self.assertFalse(list(summary_root.glob("*.md")))
        for folder in (path for path in summary_root.iterdir() if path.is_dir()):
            self.assertEqual({path.name for path in folder.glob("*.md")}, expected, folder)

    def test_root_readme_links_default_english_documents(self) -> None:
        readme = read("README.md")
        for target in (
            "docs/architecture/FRONTEND_BACKEND.md",
            "docs/data/README.md",
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
