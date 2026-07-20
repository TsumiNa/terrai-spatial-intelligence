"""Tests for the multi-scale evidence builder's source-CSV decoding."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.build_multiscale_evidence import data_as_of, read_csv_text, reconcile_facility_sources


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


def gsi_feature(
    name: str,
    designation_type: str,
    coordinates: list[float],
    *,
    common_id: str,
    hazards: list[str] | None = None,
    address: str = "神奈川県横浜市保土ケ谷区岩崎町22-1",
) -> dict:
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": coordinates},
        "properties": {
            "name": name,
            "address": address,
            "designation_type": designation_type,
            "common_id": common_id,
            "hazards": hazards or [],
            "source_updated_at": "2026-01-16",
            "retrieved_at": "2026-07-21T00:00:00+00:00",
        },
    }


def local_row(name: str, coordinates: list[float]) -> dict[str, str]:
    return {
        "Name": name,
        "Definition": "local definition",
        "Type": "地域防災拠点",
        "Address": "local address",
        "Ward": "保土ケ谷区",
        "Lon": str(coordinates[0]),
        "Lat": str(coordinates[1]),
    }


def test_national_shelters_are_base_and_local_rows_validate_or_supplement() -> None:
    gsi = [
        gsi_feature(
            "横浜市立岩崎小学校",
            "designated_shelter",
            [139.5864, 35.4467],
            common_id="S1",
        ),
        gsi_feature(
            "横浜市立岩崎中学校",
            "designated_shelter",
            [139.5853, 35.4499],
            common_id="S2",
            address="神奈川県横浜市旭区テスト町1-1",
        ),
        gsi_feature(
            "横浜市立岩崎小学校　体育館１４",
            "designated_emergency_evacuation_place",
            [139.5865, 35.4468],
            common_id="E1",
            hazards=["flood", "earthquake"],
        ),
        gsi_feature(
            "横浜市立桜台小学校　体育館１０",
            "designated_emergency_evacuation_place",
            [139.5914, 35.4502],
            common_id="E2",
            hazards=["earthquake"],
        ),
    ]
    local = [
        local_row("岩崎小学校", [139.5864, 35.4467]),
        local_row("桜台小学校", [139.5914, 35.4502]),
    ]

    records = reconcile_facility_sources(gsi, local)
    by_name = {item["properties"]["name"]: item["properties"] for item in records}

    assert len(records) == 3
    assert by_name["横浜市立岩崎小学校"]["source_reconciliation"] == "national_base_local_validated"
    assert by_name["横浜市立岩崎小学校"]["gsi_designated_hazards"] == ["earthquake", "flood"]
    assert by_name["横浜市立岩崎中学校"]["source_reconciliation"] == "national_base_only"
    assert by_name["横浜市立岩崎中学校"]["ward"] == "旭区"
    assert by_name["桜台小学校"]["source_reconciliation"] == "local_supplement_not_in_national_shelter_base"
    assert by_name["桜台小学校"]["gsi_designated_hazards"] == ["earthquake"]
    assert by_name["桜台小学校"]["gsi_emergency_source_updated_at"] == "2026-01-16"
    assert by_name["桜台小学校"]["local_source_updated_at"] == "2026-04-01"


# --- data_as_of ---------------------------------------------------------------
# The summary is a committed artifact, so its contents must be a function of the
# inputs alone. These cover the failure that motivated it: a wall-clock value
# dirtied the working tree on every rebuild.


def test_data_as_of_picks_the_latest_provenance_date() -> None:
    assert data_as_of("2026-01-16", "2026-07-20T21:25:42+00:00", "2026-04-01") == "2026-07-20"


def test_data_as_of_normalises_mixed_date_and_timestamp_formats() -> None:
    assert data_as_of("2026-07-20T23:59:59+00:00", "2026-07-20") == "2026-07-20"


def test_data_as_of_ignores_missing_values() -> None:
    assert data_as_of(None, "2026-04-01", None) == "2026-04-01"


def test_data_as_of_returns_empty_when_nothing_is_known() -> None:
    assert data_as_of() == ""
    assert data_as_of(None, None) == ""


def test_data_as_of_is_independent_of_argument_order() -> None:
    dates = ("2026-01-16", "2026-07-20", "2026-04-01")
    assert data_as_of(*dates) == data_as_of(*reversed(dates))
