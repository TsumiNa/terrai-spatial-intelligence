from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from terrai_spatial.data_tasks import BOOTSTRAP_OUTPUTS, _ordered_names, ensure_data, task_state


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def write_json(path: Path, *, geojson: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    value = {"type": "FeatureCollection", "features": []} if geojson else {}
    path.write_text(json.dumps(value), encoding="utf-8")


class DataTaskStateTests(unittest.TestCase):
    def test_joint_missing_and_stale_outputs_are_detected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            script = root / "scripts/build_joint_analysis.py"
            script.parent.mkdir(parents=True)
            script.write_text("# test\n", encoding="utf-8")
            inputs = (
                "data/yokohama/building_risk.geojson",
                "data/yokohama/road_priority.geojson",
                "data/mobara/site_cells.geojson",
            )
            outputs = (
                "data/joint/compound_corridors.geojson",
                "data/joint/resilience_hubs.geojson",
                "data/joint/solar_delivery_cells.geojson",
                "data/joint/joint_summary.json",
            )
            for relative in inputs:
                write_json(root / relative, geojson=True)
            for relative in outputs:
                write_json(root / relative, geojson=relative.endswith(".geojson"))
            for path in [script, *(root / item for item in inputs)]:
                os.utime(path, (100, 100))
            for path in (root / item for item in outputs):
                os.utime(path, (200, 200))

            self.assertEqual(task_state("joint", root).status, "ready")
            os.utime(root / inputs[0], (300, 300))
            self.assertEqual(task_state("joint", root).status, "stale")
            (root / outputs[0]).unlink()
            self.assertEqual(task_state("joint", root).status, "missing")

    def test_tile_manifest_detects_a_missing_cached_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tile = root / "data/tiles/yokohama/15/1-1.png"
            tile.parent.mkdir(parents=True)
            tile.write_bytes(b"valid tile")
            manifest = root / "data/tiles/manifest.json"
            manifest.write_text(json.dumps({"files": [str(tile.relative_to(root))]}), encoding="utf-8")
            self.assertEqual(task_state("tiles", root).status, "ready")
            tile.unlink()
            state = task_state("tiles", root)
            self.assertEqual(state.status, "missing")
            self.assertIn("1-1.png", state.reason)

    def test_corrupt_packaged_json_is_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in BOOTSTRAP_OUTPUTS:
                path = root / relative
                if path.suffix == ".csv":
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text("header\n", encoding="utf-8")
                else:
                    write_json(path, geojson=path.suffix == ".geojson")
            (root / "data/mobara/solar_summary.json").write_text("{", encoding="utf-8")
            self.assertEqual(task_state("bootstrap", root).status, "missing")

    def test_evidence_dependencies_are_ordered_before_the_task(self) -> None:
        self.assertEqual(_ordered_names(["evidence"]), ["bootstrap", "embedding", "evidence"])

    def test_missing_grid_summary_runs_the_download_and_parse_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            scripts = root / "scripts"
            scripts.mkdir()
            for name in ("fetch_tepco_grid.py", "parse_tepco_grid.py", "update_tepco_grid.py"):
                shutil.copy2(PROJECT_ROOT / "scripts" / name, scripts / name)
            source = root / "tepco-fixture.zip"
            preamble = "\n".join(["metadata"] * 6) + "\n"
            with zipfile.ZipFile(source, "w") as archive:
                archive.writestr("csv_yosochoryu_chiba_soudensen.csv", preamble)
                archive.writestr("csv_yosochoryu_chiba_hendensyo.csv", preamble)
            with patch.dict(os.environ, {"TERRAI_TEPCO_CHIBA_URL": source.as_uri()}):
                states = ensure_data(root=root, selected=["grid"], allow_network=True)
            self.assertEqual(states[-1].status, "ready")
            output = root / "data/mobara/tepco_grid_screen.json"
            self.assertTrue(output.is_file())
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["chiba_summary"]["transmission_line_rows"], 0)
            self.assertTrue((root / "data/external/tepco/download_metadata.local.json").is_file())


if __name__ == "__main__":
    unittest.main()
