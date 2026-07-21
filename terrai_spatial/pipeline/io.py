"""Atomic writes, JSON/GeoJSON validity, hashing and safe zip extraction.

The write style parameters exist so every migrated script can reproduce its
current output bytes exactly; they do not bless the style inconsistency
forever. Normalizing formats is a candidate follow-up once the committed files
are less load-bearing.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import unquote


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        try:
            handle.write(text)
        except BaseException:
            handle.close()
            temporary.unlink(missing_ok=True)
            raise
    try:
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def write_bytes_atomic(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("wb", dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        try:
            handle.write(payload)
        except BaseException:
            handle.close()
            temporary.unlink(missing_ok=True)
            raise
    try:
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def serialize_json(value: Any, *, compact: bool = False) -> str:
    if compact:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return json.dumps(value, ensure_ascii=False, indent=2)


def write_json_atomic(path: Path, value: Any, *, compact: bool = False, trailing_newline: bool = True) -> None:
    text = serialize_json(value, compact=compact)
    if trailing_newline:
        text += "\n"
    write_text_atomic(path, text)


def read_json_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"invalid {label}: {path}: {error}") from error
    if not isinstance(value, dict):
        raise RuntimeError(f"invalid {label}: root is not an object: {path}")
    return value


def json_file_failure(path: Path) -> str | None:
    """Why a JSON/GeoJSON file is invalid, or ``None`` when it is valid."""

    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return str(error)
    if path.suffix == ".geojson" and (not isinstance(value, dict) or value.get("type") != "FeatureCollection"):
        return "GeoJSON root is not a FeatureCollection"
    return None


def valid_data_file(path: Path) -> bool:
    """Non-empty; JSON parses; a ``.geojson`` root is a FeatureCollection."""

    if not path.is_file() or path.stat().st_size == 0:
        return False
    if path.suffix not in {".json", ".geojson"}:
        return True
    return json_file_failure(path) is None


def safe_relative_path(value: str, *, label: str) -> PurePosixPath:
    """A relative path that cannot escape its root, or a raised RuntimeError."""

    if not value or "\\" in value or "\x00" in value:
        raise RuntimeError(f"unsafe {label}: {value!r}")
    path = PurePosixPath(unquote(value))
    if path.is_absolute() or ".." in path.parts:
        raise RuntimeError(f"unsafe {label}: {value!r}")
    return path


def safe_extract_zip(archive_path: Path, destination: Path, *, max_member_bytes: int | None = None) -> list[Path]:
    """Extract a zip, rejecting traversal, symlinks and oversized members.

    Returns the extracted file paths in archive order. The size cap is checked
    against both the declared size and the streamed bytes, because the header
    can lie.
    """

    destination.mkdir(parents=True, exist_ok=True)
    extracted: list[Path] = []
    with zipfile.ZipFile(archive_path) as archive:
        for member in archive.infolist():
            relative = safe_relative_path(member.filename, label="ZIP member")
            if stat.S_ISLNK(member.external_attr >> 16):
                raise RuntimeError(f"unsafe ZIP member: symbolic link {member.filename!r}")
            if max_member_bytes is not None and member.file_size > max_member_bytes:
                raise RuntimeError(f"ZIP member exceeds {max_member_bytes} bytes: {member.filename!r}")
            target = destination.joinpath(*relative.parts)
            resolved = target.resolve()
            if resolved != destination.resolve() and destination.resolve() not in resolved.parents:
                raise RuntimeError(f"unsafe ZIP member: {member.filename!r}")
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as source, target.open("wb") as output:
                copied = 0
                while chunk := source.read(1024 * 1024):
                    copied += len(chunk)
                    if max_member_bytes is not None and copied > max_member_bytes:
                        raise RuntimeError(f"ZIP member exceeds {max_member_bytes} bytes: {member.filename!r}")
                    output.write(chunk)
            extracted.append(target)
    return extracted
