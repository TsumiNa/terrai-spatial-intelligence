#!/usr/bin/env python3
"""Download and safely unpack TEPCO's Chiba predicted-flow CSV archive.

The source archive is intentionally kept outside Git because TEPCO does not
publish it under an open-data licence. This script only creates a local cache.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "external" / "tepco"
ARCHIVE_NAME = "csv_yosochoryu_chiba.zip"
METADATA_NAME = "download_metadata.local.json"
OFFICIAL_PAGE = "https://www.tepco.co.jp/pg/consignment/system/index-j.html"
DEFAULT_URL = "https://www.tepco.co.jp/pg/consignment/system/pdf/csv_yosochoryu_chiba.zip"
EXPECTED_FILES = (
    "csv_yosochoryu_chiba_soudensen.csv",
    "csv_yosochoryu_chiba_hendensyo.csv",
)
MAX_ARCHIVE_BYTES = 50 * 1024 * 1024
MAX_EXTRACTED_FILE_BYTES = 25 * 1024 * 1024
USER_AGENT = "TerrAI-Spatial-Intelligence/0.3 (+https://github.com/TsumiNa/terrai-spatial-intelligence)"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temporary = Path(handle.name)
    os.replace(temporary, path)


def _download(url: str, destination: Path, *, retries: int = 3) -> dict[str, str | None]:
    last_error: Exception | None = None
    for attempt in range(retries):
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/zip"})
        try:
            with urllib.request.urlopen(request, timeout=30) as response, destination.open("wb") as output:
                total = 0
                while chunk := response.read(1024 * 1024):
                    total += len(chunk)
                    if total > MAX_ARCHIVE_BYTES:
                        raise RuntimeError(f"TEPCO archive exceeds {MAX_ARCHIVE_BYTES} bytes")
                    output.write(chunk)
                return {
                    "resolved_url": response.geturl(),
                    "http_last_modified": response.headers.get("Last-Modified"),
                    "http_etag": response.headers.get("ETag"),
                    "http_content_type": response.headers.get("Content-Type"),
                }
        except (OSError, RuntimeError, urllib.error.URLError) as error:
            last_error = error
            destination.unlink(missing_ok=True)
            if attempt + 1 < retries:
                time.sleep(0.5 * (attempt + 1))
    raise RuntimeError(f"failed to download TEPCO archive from {url}: {last_error}") from last_error


def extract_archive(archive: Path, raw_dir: Path) -> dict[str, dict[str, str | int]]:
    """Extract only the two expected basenames, rejecting missing or duplicate members."""
    if not zipfile.is_zipfile(archive):
        raise RuntimeError(f"download is not a valid ZIP archive: {archive}")
    raw_dir.mkdir(parents=True, exist_ok=True)
    extracted: dict[str, dict[str, str | int]] = {}
    with zipfile.ZipFile(archive) as bundle:
        members: dict[str, zipfile.ZipInfo] = {}
        for info in bundle.infolist():
            basename = Path(info.filename).name
            if basename not in EXPECTED_FILES:
                continue
            if basename in members:
                raise RuntimeError(f"duplicate expected file in TEPCO archive: {basename}")
            members[basename] = info
        missing = [name for name in EXPECTED_FILES if name not in members]
        if missing:
            raise RuntimeError(f"TEPCO archive is missing expected files: {', '.join(missing)}")
        oversized = [name for name, info in members.items() if info.file_size > MAX_EXTRACTED_FILE_BYTES]
        if oversized:
            raise RuntimeError(f"TEPCO archive contains oversized files: {', '.join(oversized)}")

        temporary_paths: list[tuple[Path, Path]] = []
        try:
            for name in EXPECTED_FILES:
                target = raw_dir / name
                with bundle.open(members[name]) as source, tempfile.NamedTemporaryFile(
                    "wb", dir=raw_dir, delete=False
                ) as output:
                    copied = 0
                    while chunk := source.read(1024 * 1024):
                        copied += len(chunk)
                        if copied > MAX_EXTRACTED_FILE_BYTES:
                            raise RuntimeError(f"TEPCO archive member exceeds size limit: {name}")
                        output.write(chunk)
                    temporary = Path(output.name)
                if temporary.stat().st_size == 0:
                    raise RuntimeError(f"TEPCO archive member is empty: {name}")
                temporary_paths.append((temporary, target))
            for temporary, target in temporary_paths:
                os.replace(temporary, target)
                extracted[target.name] = {
                    "bytes": target.stat().st_size,
                    "sha256": sha256(target),
                }
        finally:
            for temporary, _ in temporary_paths:
                temporary.unlink(missing_ok=True)
    return extracted


def _cached_files_are_complete(raw_dir: Path) -> bool:
    return all((raw_dir / name).is_file() and (raw_dir / name).stat().st_size > 0 for name in EXPECTED_FILES)


def fetch_tepco_data(
    *,
    raw_dir: Path = RAW,
    url: str = DEFAULT_URL,
    official_page: str = OFFICIAL_PAGE,
    force: bool = False,
    offline: bool = False,
) -> dict:
    raw_dir.mkdir(parents=True, exist_ok=True)
    archive = raw_dir / ARCHIVE_NAME
    metadata_path = raw_dir / METADATA_NAME
    cached_files_complete = _cached_files_are_complete(raw_dir)
    downloaded_files: dict[str, dict[str, str | int]] | None = None

    if offline and cached_files_complete:
        if metadata_path.is_file():
            return json.loads(metadata_path.read_text(encoding="utf-8"))
        source = "existing local CSV cache"
        headers: dict[str, str | None] = {}
    elif offline and archive.is_file():
        source = "existing local ZIP cache"
        headers = {}
    elif offline:
        raise RuntimeError(
            "TEPCO grid cache is incomplete and offline mode forbids downloading; "
            "run again without --offline"
        )
    elif cached_files_complete and not force:
        if metadata_path.is_file():
            return json.loads(metadata_path.read_text(encoding="utf-8"))
        source = "existing local CSV cache"
        headers = {}
    elif archive.is_file() and not force:
        source = "existing local ZIP cache"
        headers = {}
    else:
        with tempfile.NamedTemporaryFile("wb", dir=raw_dir, delete=False) as handle:
            temporary_archive = Path(handle.name)
        try:
            headers = _download(url, temporary_archive)
            if not zipfile.is_zipfile(temporary_archive):
                raise RuntimeError("TEPCO response is not a ZIP archive")
            downloaded_files = extract_archive(temporary_archive, raw_dir)
            os.replace(temporary_archive, archive)
        finally:
            temporary_archive.unlink(missing_ok=True)
        source = "official download"

    if downloaded_files is not None:
        files = downloaded_files
    elif archive.is_file() and (source == "existing local ZIP cache" or force or not cached_files_complete):
        files = extract_archive(archive, raw_dir)
    else:
        files = {
            name: {"bytes": (raw_dir / name).stat().st_size, "sha256": sha256(raw_dir / name)}
            for name in EXPECTED_FILES
        }

    downloaded_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    metadata = {
        "schema_version": 1,
        "source": "TEPCO Power Grid - 系統の予想潮流等に関する情報（千葉県CSV）",
        "official_page": official_page,
        "download_url": url,
        "resolved_url": headers.get("resolved_url", url),
        "downloaded_at": downloaded_at,
        "retrieval": source,
        "http_last_modified": headers.get("http_last_modified"),
        "http_etag": headers.get("http_etag"),
        "archive": (
            {"path": f"data/external/tepco/{ARCHIVE_NAME}", "bytes": archive.stat().st_size, "sha256": sha256(archive)}
            if archive.is_file()
            else None
        ),
        "files": files,
        "rights_note": "Local internal cache only; do not commit or redistribute without confirming permission with TEPCO.",
    }
    _atomic_json(metadata_path, metadata)
    print(
        f"TEPCO cache ready: {len(files)} CSV files; retrieval={source}; "
        f"metadata={metadata_path.relative_to(ROOT) if ROOT in metadata_path.parents else metadata_path}"
    )
    return metadata


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="download the current official archive even if cached")
    parser.add_argument("--offline", action="store_true", help="use only an existing local ZIP/CSV cache")
    parser.add_argument("--url", default=os.environ.get("TERRAI_TEPCO_CHIBA_URL", DEFAULT_URL))
    return parser


def main() -> None:
    args = build_parser().parse_args()
    fetch_tepco_data(url=args.url, force=args.force, offline=args.offline)


if __name__ == "__main__":
    main()
