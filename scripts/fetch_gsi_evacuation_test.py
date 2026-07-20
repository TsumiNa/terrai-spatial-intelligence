"""Tests for the GSI evacuation downloader's deterministic normalization."""

from __future__ import annotations

import json

from scripts.fetch_gsi_evacuation import build_dataset, publication_record


HISTORY = b"14100,\xe7\xa5\x9e\xe5\xa5\x88\xe5\xb7\x9d\xe7\x9c\x8c\xe6\xa8\xaa\xe6\xb5\x9c\xe5\xb8\x82,2017-02-22,2026-01-16,,\r\n"


def collection(properties: dict) -> bytes:
    return json.dumps(
        {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [139.58, 35.44]},
                    "properties": properties,
                }
            ],
        },
        ensure_ascii=False,
    ).encode()


def test_publication_record_preserves_gsi_source_dates() -> None:
    assert publication_record(HISTORY) == {
        "municipality_code": "14100",
        "municipality_name": "神奈川県横浜市",
        "publication_started_at": "2017-02-22",
        "source_updated_at": "2026-01-16",
        "publication_note": None,
        "publication_status": None,
    }


def test_build_dataset_normalizes_designations_hazards_and_timestamps() -> None:
    dataset, metadata = build_dataset(
        collection(
            {
                "NO": "1",
                "共通ID": "S1",
                "施設・場所名": "横浜市立岩崎小学校",
                "住所": "神奈川県横浜市保土ケ谷区岩崎町22-1",
                "指定緊急避難場所との住所同一": "1",
            }
        ),
        collection(
            {
                "NO": "2",
                "共通ID": "E1",
                "施設・場所名": "横浜市立岩崎小学校　体育館１４",
                "住所": "神奈川県横浜市保土ケ谷区岩崎町22-1",
                "洪水": "1",
                "地震": "1",
                "津波": "",
            }
        ),
        HISTORY,
        retrieved_at="2026-07-21T00:00:00+00:00",
    )

    assert metadata["feature_counts"] == {
        "designated_shelter": 1,
        "designated_emergency_evacuation_place": 1,
    }
    assert metadata["source_updated_at"] == "2026-01-16"
    assert metadata["retrieved_at"] == "2026-07-21T00:00:00+00:00"
    shelter, emergency = dataset["features"]
    assert shelter["properties"]["designation_type"] == "designated_shelter"
    assert shelter["properties"]["same_address_with_other_designation"] is True
    assert emergency["properties"]["hazards"] == ["flood", "earthquake"]
    assert emergency["properties"]["source_updated_at"] == "2026-01-16"
    assert emergency["properties"]["retrieved_at"] == "2026-07-21T00:00:00+00:00"
