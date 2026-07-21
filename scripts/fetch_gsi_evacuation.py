#!/usr/bin/env python3
"""Download and normalize GSI designated evacuation data for Yokohama."""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from terrai_spatial.pipeline.http import download_bytes  # noqa: E402
from terrai_spatial.pipeline.io import write_json_atomic  # noqa: E402
from terrai_spatial.pipeline.provenance import utc_timestamp  # noqa: E402

OUT_DIR = ROOT / "data" / "external" / "gsi_evacuation"
OUTPUT = OUT_DIR / "yokohama_evacuation.geojson"
METADATA = OUT_DIR / "metadata.json"
MUNICIPALITY_CODE = "14100"
BASE_URL = "https://hinanmap.gsi.go.jp/hinanjocp/defaultFtpData"
SOURCE_URLS = {
    "designated_shelter": f"{BASE_URL}/geoJSON/{MUNICIPALITY_CODE}_1.geojson",
    "designated_emergency_evacuation_place": f"{BASE_URL}/geoJSON/{MUNICIPALITY_CODE}_2.geojson",
    "publication_history": f"{BASE_URL}/publicHistoryCSV/publicHistoryListData.csv",
}

HAZARD_FIELDS = {
    "洪水": "flood",
    "崖崩れ、土石流及び地滑り": "landslide_debris_flow",
    "高潮": "storm_surge",
    "地震": "earthquake",
    "津波": "tsunami",
    "大規模な火事": "large_fire",
    "内水氾濫": "inland_flooding",
    "火山現象": "volcanic_phenomena",
}


def publication_record(payload: bytes, municipality_code: str = MUNICIPALITY_CODE) -> dict[str, str | None]:
    text = payload.decode("utf-8-sig")
    for row in csv.reader(io.StringIO(text, newline="")):
        if row and row[0] == municipality_code:
            padded = [*row, "", "", "", "", "", ""]
            return {
                "municipality_code": padded[0],
                "municipality_name": padded[1],
                "publication_started_at": padded[2] or None,
                "source_updated_at": padded[3] or None,
                "publication_note": padded[4] or None,
                "publication_status": padded[5] or None,
            }
    raise ValueError(f"GSI publication history has no municipality {municipality_code}")


def normalize_feature(
    feature: dict,
    designation_type: str,
    *,
    source_updated_at: str | None,
    retrieved_at: str,
) -> dict:
    props = feature.get("properties", {})
    hazards = [english for japanese, english in HAZARD_FIELDS.items() if props.get(japanese) == "1"]
    normalized = {
        "municipality_code": MUNICIPALITY_CODE,
        "designation_type": designation_type,
        "common_id": props.get("共通ID"),
        "name": props.get("施設・場所名"),
        "address": props.get("住所"),
        "hazards": hazards,
        "same_address_with_other_designation": props.get("指定緊急避難場所との住所同一") == "1"
        or props.get("指定避難所との住所同一") == "1",
        "accepted_population": props.get("受入対象者"),
        "additional_information": props.get("その他市町村長が必要と認める事項"),
        "notes": props.get("備考") or None,
        "source_scope": "national",
        "source_id": "gsi_designated_evacuation",
        "source_updated_at": source_updated_at,
        "retrieved_at": retrieved_at,
        "source_url": SOURCE_URLS[designation_type],
    }
    return {
        "type": "Feature",
        "id": props.get("共通ID") or f"gsi-{designation_type}-{props.get('NO')}",
        "geometry": feature.get("geometry"),
        "properties": normalized,
    }


def build_dataset(
    shelter_payload: bytes,
    emergency_payload: bytes,
    history_payload: bytes,
    *,
    retrieved_at: str,
) -> tuple[dict, dict]:
    history = publication_record(history_payload)
    source_updated_at = history["source_updated_at"]
    inputs = {
        "designated_shelter": json.loads(shelter_payload.decode("utf-8-sig")),
        "designated_emergency_evacuation_place": json.loads(emergency_payload.decode("utf-8-sig")),
    }
    features = [
        normalize_feature(
            feature,
            designation_type,
            source_updated_at=source_updated_at,
            retrieved_at=retrieved_at,
        )
        for designation_type, collection in inputs.items()
        for feature in collection.get("features", [])
    ]
    counts = {
        designation_type: len(collection.get("features", []))
        for designation_type, collection in inputs.items()
    }
    dataset = {
        "type": "FeatureCollection",
        "metadata": {
            **history,
            "retrieved_at": retrieved_at,
            "source_scope": "national",
            "source_urls": SOURCE_URLS,
            "feature_counts": counts,
        },
        "features": features,
    }
    metadata = {
        **dataset["metadata"],
        "total_features": len(features),
        "output": str(OUTPUT.relative_to(ROOT)),
        "license": "GSI content terms / Public Data License 1.0 unless otherwise stated",
        "use_notice": "Confirm the latest designation and operational details with the municipality before emergency use.",
    }
    return dataset, metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="refresh even when both outputs already exist")
    args = parser.parse_args()
    if OUTPUT.is_file() and METADATA.is_file() and not args.force:
        print(f"GSI evacuation data already available: {OUTPUT.relative_to(ROOT)}")
        return

    retrieved_at = utc_timestamp()
    dataset, metadata = build_dataset(
        download_bytes(SOURCE_URLS["designated_shelter"], timeout=60),
        download_bytes(SOURCE_URLS["designated_emergency_evacuation_place"], timeout=60),
        download_bytes(SOURCE_URLS["publication_history"], timeout=60),
        retrieved_at=retrieved_at,
    )
    write_json_atomic(OUTPUT, dataset, compact=True)
    write_json_atomic(METADATA, metadata)
    print(
        f"Wrote {metadata['total_features']} GSI features "
        f"(source updated {metadata['source_updated_at']}) to {OUTPUT.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
