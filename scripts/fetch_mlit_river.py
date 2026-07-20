"""Fetch MLIT W05 river data into a Git-ignored non-commercial cache."""

from __future__ import annotations

import argparse
import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from fetch_mlit_foundation import Archive, Dataset, KSJ, ROOT, _download, _extract, _layers, _read_features

OUTPUT = ROOT / "data/external/mlit_restricted"
RIVER = Dataset(
    "river", "ksj-w05-river", "river.local.geojson", "2008",
    "NON-COMMERCIAL USE ONLY under the dataset page's legacy terms",
    (Archive(f"{KSJ}/W05/W05-08/W05-08_14_GML.zip", "yokohama"), Archive(f"{KSJ}/W05/W05-08/W05-08_12_GML.zip", "mobara")),
)


def build() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    retrieved_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    features, downloads = [], []
    with tempfile.TemporaryDirectory(prefix="terrai-mlit-river-") as temporary:
        temp = Path(temporary)
        for index, archive in enumerate(RIVER.archives):
            zipped = temp / f"river-{index}.zip"
            details = _download(archive.url, zipped)
            extracted = temp / str(index)
            extracted.mkdir()
            _extract(zipped, extracted)
            layers = _layers(extracted, "preferred")
            for layer in layers:
                features.extend(_read_features(layer, RIVER, archive, retrieved_at))
            downloads.append({"url": archive.url, **details})
    collection = {"type": "FeatureCollection", "name": RIVER.dataset_id, "metadata": {"retrieved_at": retrieved_at, "license": RIVER.license, "commercial_api": False}, "features": features}
    (OUTPUT / RIVER.output).write_text(json.dumps(collection, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (OUTPUT / "metadata.local.json").write_text(json.dumps({"retrieved_at": retrieved_at, "downloads": downloads, "feature_count": len(features)}, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(features)} river features to a Git-ignored non-commercial cache")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    if args.offline:
        if not (OUTPUT / RIVER.output).is_file():
            raise SystemExit("river cache is absent and cannot be restored offline")
        return
    build()


if __name__ == "__main__":
    main()
