#!/usr/bin/env python3
"""Normalize TEPCO Chiba public predicted-flow / capacity CSVs for the PoC."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "external" / "tepco"
OUTPUT = ROOT / "data" / "mobara" / "tepco_grid_screen.json"


def number(value: str):
    cleaned = value.replace(",", "").strip()
    if cleaned in {"", "-"}:
        return None
    try:
        return float(cleaned) if "." in cleaned else int(cleaned)
    except ValueError:
        return None


def rows(path: Path) -> list[list[str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return [row for row in csv.reader(handle)][6:]


def parse_lines(path: Path) -> list[dict]:
    result = []
    for row in rows(path):
        if len(row) < 21 or not row[0].strip():
            continue
        result.append(
            {
                "equipment_id": row[0],
                "name": row[1],
                "voltage_kv": number(row[2]),
                "circuits": number(row[3]),
                "equipment_capacity_raw": number(row[4]),
                "operating_capacity_before_control_mw": number(row[5]),
                "existing_olr_mw": number(row[6]),
                "operating_capacity_mw": number(row[7]),
                "constraint": row[8],
                "flow_from": row[9],
                "flow_to": row[11],
                "predicted_flow_mw": number(row[12]),
                "spare_own_mw": number(row[13]),
                "spare_with_upstream_mw": number(row[14]),
                "n_minus_1_applicable": row[15],
                "n_minus_1_control_mw": number(row[16]),
                "normal_output_control_possible": row[17] == "有り",
                "affected_equipment": row[18],
                "upstream_constraints": row[19],
            }
        )
    return result


def parse_transformers(path: Path) -> list[dict]:
    result = []
    for row in rows(path):
        if len(row) < 19 or not row[0].strip():
            continue
        result.append(
            {
                "equipment_id": row[0],
                "name": row[1],
                "voltage_kv": row[2],
                "units": number(row[3]),
                "equipment_capacity_raw": number(row[4]),
                "operating_capacity_mw": number(row[5]),
                "constraint": row[6],
                "predicted_flow_mw": number(row[10]),
                "spare_own_mw": number(row[11]),
                "spare_with_upstream_mw": number(row[12]),
                "n_minus_1_applicable": row[13],
                "n_minus_1_control_mw": number(row[14]),
                "normal_output_control_possible": row[15] == "有り",
                "affected_equipment": row[16],
                "upstream_constraints": row[17],
            }
        )
    return result


def main() -> None:
    lines = parse_lines(RAW / "csv_yosochoryu_chiba_soudensen.csv")
    transformers = parse_transformers(RAW / "csv_yosochoryu_chiba_hendensyo.csv")
    mobara_lines = [item for item in lines if "茂原" in " ".join(str(value) for value in item.values())]
    mobara_transformers = [item for item in transformers if "茂原" in item["name"]]
    local_station = next((item for item in mobara_transformers if item["name"] == "茂原"), None)
    value = {
        "published_at": "2026-06-22",
        "downloaded_at": "2026-07-20",
        "source": "TEPCO Power Grid - 系統の予想潮流等に関する情報（千葉県CSV）",
        "source_url": "https://www.tepco.co.jp/pg/consignment/system/index-j.html",
        "raw_files": [
            "data/external/tepco/csv_yosochoryu_chiba_soudensen.csv",
            "data/external/tepco/csv_yosochoryu_chiba_hendensyo.csv",
        ],
        "chiba_summary": {
            "transmission_line_rows": len(lines),
            "transformer_rows": len(transformers),
            "lines_with_normal_output_control_possible": sum(item["normal_output_control_possible"] for item in lines),
            "transformers_with_normal_output_control_possible": sum(item["normal_output_control_possible"] for item in transformers),
        },
        "mobara_matches": {
            "lines": mobara_lines,
            "transformers": mobara_transformers,
        },
        "mobara_screen": {
            "station": local_station["name"] if local_station else None,
            "spare_own_mw": local_station["spare_own_mw"] if local_station else None,
            "spare_with_upstream_mw": local_station["spare_with_upstream_mw"] if local_station else None,
            "normal_output_control_possible": local_station["normal_output_control_possible"] if local_station else None,
            "screening_status": "upstream_constrained" if local_station and local_station["spare_with_upstream_mw"] == 0 else "review",
            "interpretation": "公开快照显示茂原配电用变电所自身尚有容量代理，但考虑上位系统后为0 MW，且存在平常时出力控制可能。",
        },
        "important_note": "公开数值只是选址筛查证据，不是接续検討结果；CSV没有可直接用于宗地空间连接的完整设备几何。",
    }
    OUTPUT.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Parsed {len(lines)} line rows and {len(transformers)} transformer rows; Mobara matches: {len(mobara_lines)} lines / {len(mobara_transformers)} transformers")


if __name__ == "__main__":
    main()
