from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from scripts.fetch_tepco_grid import EXPECTED_FILES, fetch_tepco_data


def make_archive(path: Path, *, missing: bool = False) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        names = EXPECTED_FILES[:-1] if missing else EXPECTED_FILES
        for name in names:
            archive.writestr(name, f"test content for {name}\n".encode())
        archive.writestr("unrelated.txt", b"must not be extracted")


def test_downloads_extracts_only_expected_files_and_records_provenance(tmp_path: Path) -> None:
    source = tmp_path / "source.zip"
    raw = tmp_path / "raw"
    make_archive(source)

    metadata = fetch_tepco_data(raw_dir=raw, url=source.as_uri(), force=True)

    assert set(metadata["files"]) == set(EXPECTED_FILES)
    assert metadata["retrieval"] == "official download"
    assert metadata["archive"]["sha256"]
    assert not (raw / "unrelated.txt").exists()
    for name in EXPECTED_FILES:
        assert (raw / name).is_file()
        assert metadata["files"][name]["sha256"]
    saved = json.loads((raw / "download_metadata.local.json").read_text(encoding="utf-8"))
    assert saved["download_url"] == source.as_uri()


def test_offline_mode_rejects_an_incomplete_cache(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="offline mode"):
        fetch_tepco_data(raw_dir=tmp_path, offline=True)


def test_archive_missing_an_expected_csv_does_not_pass_validation(tmp_path: Path) -> None:
    source = tmp_path / "source.zip"
    make_archive(source, missing=True)
    with pytest.raises(RuntimeError, match="missing expected files"):
        fetch_tepco_data(raw_dir=tmp_path / "raw", url=source.as_uri(), force=True)
    assert not (tmp_path / "raw/csv_yosochoryu_chiba.zip").exists()
