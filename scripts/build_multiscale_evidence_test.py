"""Tests for the multi-scale evidence builder's source-CSV decoding."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.build_multiscale_evidence import read_csv_text


HEADER = "Type,Definition,Name,Address,Lat,Lon,Kana,Ward,WardCode\r\n"
ROW = "地域防災拠点,被災した住民の避難生活の場所、情報受伝達、備蓄機能を備えた拠点です。,生麦小学校,神奈川県横浜市鶴見区生麦四丁目15-1,35.49547584,139.6710972,ナマムギショウガッコウ,鶴見区,01\r\n"
SAMPLE = HEADER + ROW


@pytest.fixture
def write_csv(tmp_path: Path):
    def _write(payload: bytes) -> Path:
        path = tmp_path / "hinanjo.csv"
        path.write_bytes(payload)
        return path

    return _write


def test_shift_jis_source_is_decoded_and_rewritten_as_utf8(write_csv) -> None:
    path = write_csv(SAMPLE.encode("cp932"))
    assert read_csv_text(path) == SAMPLE
    assert path.read_bytes() == SAMPLE.encode("utf-8")


def test_utf8_source_is_returned_unchanged_on_disk(write_csv) -> None:
    payload = SAMPLE.encode("utf-8")
    path = write_csv(payload)
    assert read_csv_text(path) == SAMPLE
    assert path.read_bytes() == payload


def test_utf8_bom_is_stripped_without_rewriting_the_file(write_csv) -> None:
    payload = SAMPLE.encode("utf-8-sig")
    path = write_csv(payload)
    assert read_csv_text(path) == SAMPLE
    assert path.read_bytes() == payload


def test_converted_file_is_stable_when_read_again(write_csv) -> None:
    path = write_csv(SAMPLE.encode("cp932"))
    read_csv_text(path)
    assert read_csv_text(path) == SAMPLE
    assert path.read_bytes() == SAMPLE.encode("utf-8")


def test_crlf_line_endings_survive_conversion(write_csv) -> None:
    path = write_csv(SAMPLE.encode("cp932"))
    read_csv_text(path)
    assert b"\r\n" in path.read_bytes()
    assert b"\n\n" not in path.read_bytes()


def test_empty_source_returns_empty_text(write_csv) -> None:
    assert read_csv_text(write_csv(b"")) == ""


def test_source_in_neither_encoding_raises(write_csv) -> None:
    # 0x81 is a Shift_JIS lead byte, and 0x81 0x20 is a valid pair in neither encoding.
    path = write_csv(b"Type\r\n\x81\x20\r\n")
    with pytest.raises(UnicodeDecodeError):
        read_csv_text(path)
