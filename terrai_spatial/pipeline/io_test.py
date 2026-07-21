from __future__ import annotations

import hashlib
import json
import stat
import zipfile
from pathlib import Path

import pytest

from terrai_spatial.pipeline import io


def test_write_json_atomic_reproduces_every_committed_style(tmp_path: Path) -> None:
    value = {"name": "テスト", "count": 2}

    io.write_json_atomic(tmp_path / "indented.json", value)
    io.write_json_atomic(tmp_path / "compact.json", value, compact=True)
    io.write_json_atomic(tmp_path / "bare.json", value, compact=True, trailing_newline=False)

    assert (tmp_path / "indented.json").read_text(encoding="utf-8") == (
        json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    )
    assert (tmp_path / "compact.json").read_text(encoding="utf-8") == (
        json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n"
    )
    assert (tmp_path / "bare.json").read_text(encoding="utf-8") == json.dumps(
        value, ensure_ascii=False, separators=(",", ":")
    )


def test_a_crash_between_write_and_rename_leaves_the_original_intact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "value.json"
    io.write_json_atomic(target, {"generation": 1})

    def broken_replace(source: object, destination: object) -> None:
        raise OSError("simulated crash")

    monkeypatch.setattr(io.os, "replace", broken_replace)
    with pytest.raises(OSError, match="simulated crash"):
        io.write_json_atomic(target, {"generation": 2})

    assert json.loads(target.read_text(encoding="utf-8")) == {"generation": 1}
    assert list(tmp_path.iterdir()) == [target]


def test_read_json_object_names_the_label_on_failure(tmp_path: Path) -> None:
    path = tmp_path / "broken.json"
    path.write_text("{", encoding="utf-8")
    with pytest.raises(RuntimeError, match="invalid retrieval manifest"):
        io.read_json_object(path, label="retrieval manifest")

    path.write_text("[1, 2]", encoding="utf-8")
    with pytest.raises(RuntimeError, match="root is not an object"):
        io.read_json_object(path, label="retrieval manifest")


def test_validity_check_covers_missing_empty_broken_and_non_collection_files(tmp_path: Path) -> None:
    assert not io.valid_data_file(tmp_path / "absent.json")

    empty = tmp_path / "empty.json"
    empty.touch()
    assert not io.valid_data_file(empty)

    broken = tmp_path / "broken.geojson"
    broken.write_text("{", encoding="utf-8")
    assert not io.valid_data_file(broken)

    wrong_root = tmp_path / "wrong.geojson"
    wrong_root.write_text(json.dumps({"type": "Feature"}), encoding="utf-8")
    assert io.json_file_failure(wrong_root) == "GeoJSON root is not a FeatureCollection"

    list_root = tmp_path / "list.geojson"
    list_root.write_text("[]", encoding="utf-8")
    assert not io.valid_data_file(list_root)

    collection = tmp_path / "ok.geojson"
    collection.write_text(json.dumps({"type": "FeatureCollection", "features": []}), encoding="utf-8")
    assert io.valid_data_file(collection)

    binary = tmp_path / "tile.png"
    binary.write_bytes(b"\x89PNG")
    assert io.valid_data_file(binary)


def test_file_sha256_streams_the_expected_digest(tmp_path: Path) -> None:
    path = tmp_path / "payload.bin"
    path.write_bytes(b"payload")
    assert io.file_sha256(path) == hashlib.sha256(b"payload").hexdigest()


def test_safe_extract_zip_rejects_traversal_absolute_and_symlink_members(tmp_path: Path) -> None:
    traversal = tmp_path / "traversal.zip"
    with zipfile.ZipFile(traversal, "w") as archive:
        archive.writestr("../escape.txt", "bad")
    with pytest.raises(RuntimeError, match="unsafe ZIP member"):
        io.safe_extract_zip(traversal, tmp_path / "out1")
    assert not (tmp_path / "escape.txt").exists()

    absolute = tmp_path / "absolute.zip"
    with zipfile.ZipFile(absolute, "w") as archive:
        archive.writestr("/etc/escape.txt", "bad")
    with pytest.raises(RuntimeError, match="unsafe ZIP member"):
        io.safe_extract_zip(absolute, tmp_path / "out2")

    dot = tmp_path / "dot.zip"
    with zipfile.ZipFile(dot, "w") as archive:
        archive.writestr("./", b"")
    with pytest.raises(RuntimeError, match="unsafe ZIP member"):
        io.safe_extract_zip(dot, tmp_path / "out-dot")

    symlink = tmp_path / "symlink.zip"
    with zipfile.ZipFile(symlink, "w") as archive:
        info = zipfile.ZipInfo("link")
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        archive.writestr(info, "target")
    with pytest.raises(RuntimeError, match="symbolic link"):
        io.safe_extract_zip(symlink, tmp_path / "out3")


def test_safe_extract_zip_enforces_the_member_size_cap(tmp_path: Path) -> None:
    archive_path = tmp_path / "large.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("large.bin", b"x" * 64)

    with pytest.raises(RuntimeError, match="exceeds 16 bytes"):
        io.safe_extract_zip(archive_path, tmp_path / "out", max_member_bytes=16)

    extracted = io.safe_extract_zip(archive_path, tmp_path / "ok", max_member_bytes=1024)
    assert extracted == [tmp_path / "ok" / "large.bin"]
    assert extracted[0].read_bytes() == b"x" * 64
