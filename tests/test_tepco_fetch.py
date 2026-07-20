from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.fetch_tepco_grid import EXPECTED_FILES, fetch_tepco_data


class TepcoFetchTests(unittest.TestCase):
    def make_archive(self, path: Path, *, missing: bool = False) -> None:
        with zipfile.ZipFile(path, "w") as archive:
            names = EXPECTED_FILES[:-1] if missing else EXPECTED_FILES
            for name in names:
                archive.writestr(name, f"test content for {name}\n".encode())
            archive.writestr("unrelated.txt", b"must not be extracted")

    def test_downloads_extracts_only_expected_files_and_records_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.zip"
            raw = root / "raw"
            self.make_archive(source)

            metadata = fetch_tepco_data(raw_dir=raw, url=source.as_uri(), force=True)

            self.assertEqual(set(metadata["files"]), set(EXPECTED_FILES))
            self.assertEqual(metadata["retrieval"], "official download")
            self.assertTrue(metadata["archive"]["sha256"])
            self.assertFalse((raw / "unrelated.txt").exists())
            for name in EXPECTED_FILES:
                self.assertTrue((raw / name).is_file())
                self.assertTrue(metadata["files"][name]["sha256"])
            saved = json.loads((raw / "download_metadata.local.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["download_url"], source.as_uri())

    def test_offline_mode_rejects_an_incomplete_cache(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(RuntimeError, "offline mode"):
                fetch_tepco_data(raw_dir=Path(directory), offline=True)

    def test_archive_missing_an_expected_csv_does_not_pass_validation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.zip"
            self.make_archive(source, missing=True)
            with self.assertRaisesRegex(RuntimeError, "missing expected files"):
                fetch_tepco_data(raw_dir=root / "raw", url=source.as_uri(), force=True)
            self.assertFalse((root / "raw/csv_yosochoryu_chiba.zip").exists())


if __name__ == "__main__":
    unittest.main()
