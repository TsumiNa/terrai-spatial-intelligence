"""Download and subset the wide-scope MLIT foundation datasets for Kanto.

The demo-scope products under ``data/mlit`` stay committed and untouched; this
script writes the same ten datasets acquired through the mainland-Kanto window
into ``data/external/mlit_wide`` — a gitignored reproducible cache, the same
category as the TEPCO CSVs and the PLATEAU archives. Outputs are streamed one
feature at a time because the land-use mesh alone is on the order of two
million features (see docs/refactor/kanto-foundation-coverage/00-overview.md).
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterator

import fiona
from fiona.transform import transform_geom

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.fetch_mlit_foundation import (  # noqa: E402
    DATASETS as DEMO_DATASETS,
    KOKJO,
    KSJ,
    Archive,
    Dataset,
    _bbox_in_crs,
    _json_value,
    _layers,
)
from terrai_spatial.pipeline.http import download_file  # noqa: E402
from terrai_spatial.pipeline.io import serialize_json, safe_extract_zip, write_json_atomic  # noqa: E402
from terrai_spatial.pipeline.provenance import utc_timestamp  # noqa: E402
from terrai_spatial.pipeline.regions import MLIT_WIDE_BOUNDS  # noqa: E402

OUTPUT = ROOT / "data/external/mlit_wide"
CONTEXTS = MLIT_WIDE_BOUNDS
SCOPE = "TerrAI Kanto wide acquisition: mainland Tokyo, Kanagawa, Chiba and Saitama"

PREFECTURES = ("11", "12", "13", "14")  # Saitama, Chiba, Tokyo, Kanagawa

# Sheet-by-sheet sources cover only what the upstream surveys digitised; these
# are every available Kanto sheet, and the data cards state the gaps.
F3_SHEETS = (
    "Tokyoseihokubu", "Tokyoseinanbu", "Tokyotohokubu", "Tokyotonanbu",
    "Hachioji", "Ome", "Kawagoe", "Omiya", "Noda", "Sakura", "Chiba",
    "Yokohama", "Yokosuka", "Fujisawa", "Hiratsuka",
)
LAND_HISTORY_SHEETS = (
    "533902", "533904", "533922", "533924", "533926", "533942", "533944",
    "533946", "533962", "533964", "533966", "533977", "534020", "534040",
)
LAND_USE_MESHES = ("5238", "5239", "5240", "5338", "5339", "5340", "5439", "5440")
LAND_HISTORY_ROOT = f"{KOKJO}/inspect/landclassification/land/land_history_2011/mapdata"


def _demo(key: str) -> Dataset:
    for dataset in DEMO_DATASETS:
        if dataset.key == key:
            return dataset
    raise KeyError(key)


def _wide(key: str, archives: tuple[Archive, ...]) -> Dataset:
    """The wide table inherits everything but the archives from the demo table,
    so ids, vintages and licences cannot drift between the two scopes."""

    demo = _demo(key)
    return Dataset(
        demo.key, demo.dataset_id, demo.output, demo.source_updated_at,
        demo.license, archives, demo.include,
    )


def _per_prefecture(template: str) -> tuple[Archive, ...]:
    return tuple(Archive(template.format(code=code), "kanto") for code in PREFECTURES)


WIDE_DATASETS = (
    _wide("landClassification50k", tuple(Archive(f"{KOKJO}/tochimizu/F3/GIS/{sheet}.zip", "kanto") for sheet in F3_SHEETS)),
    _wide("floodHistory", (Archive(f"{KOKJO}/tochimizu/FC/GIS/1896_2019_sinsui_add24.zip", "kanto"),)),
    _wide("landHistory", tuple(Archive(f"{LAND_HISTORY_ROOT}/{sheet}/{sheet}_gisdata.zip", "kanto") for sheet in LAND_HISTORY_SHEETS)),
    _wide("landslideWarning", _per_prefecture(f"{KSJ}/A33/A33-25/A33-25_{{code}}_GEOJSON.zip")),
    _wide("multistageFlood", (Archive(f"{KSJ}/A53/A53-25/A53-25_83_GEOJSON.zip", "kanto"),)),
    _wide("publishedLandPrice", _per_prefecture(f"{KSJ}/L01/L01-26/L01-26_{{code}}_GML.zip")),
    _wide("embankmentRegulation", _per_prefecture(f"{KSJ}/A56/A56-25/A56-25_{{code}}_GML.zip")),
    _wide("railway", (Archive(f"{KSJ}/N02/N02-25/N02-25_GML.zip", "kanto"),)),
    # Primary mesh 5238 is clipped to Kanagawa's Hakone-west sliver instead of
    # ingesting a block of Shizuoka; every other sheet uses the Kanto window.
    _wide("landUseMesh", tuple(
        Archive(f"{KSJ}/L03-b/L03-b-21/L03-b-21_{mesh}-jgd2011_GML.zip", "hakone_west" if mesh == "5238" else "kanto")
        for mesh in LAND_USE_MESHES
    )),
    _wide("prefecturalLandPrice", _per_prefecture(f"{KSJ}/L02/L02-25/L02-25_{{code}}_GML.zip")),
)


class StreamedCollection:
    """A compact FeatureCollection written feature-by-feature, atomically.

    Byte-compatible with ``write_json_atomic(compact=True,
    trailing_newline=False)`` for the same envelope and features, without ever
    holding more than one feature in memory.
    """

    def __init__(self, path: Path, name: str, metadata: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._path = path
        self._temporary = path.with_name(path.name + ".part")
        self._handle = self._temporary.open("w", encoding="utf-8")
        envelope = serialize_json({"type": "FeatureCollection", "name": name, "metadata": metadata}, compact=True)
        self._handle.write(envelope[:-1] + ',"features":[')
        self.count = 0

    def add(self, feature: dict[str, Any]) -> None:
        if self.count:
            self._handle.write(",")
        self._handle.write(serialize_json(feature, compact=True))
        self.count += 1

    def close(self) -> None:
        self._handle.write("]}")
        self._handle.close()
        os.replace(self._temporary, self._path)

    def discard(self) -> None:
        self._handle.close()
        self._temporary.unlink(missing_ok=True)


def _iter_features(path: Path, dataset: Dataset, archive: Archive, retrieved_at: str) -> Iterator[dict[str, Any]]:
    with fiona.open(path) as source:
        source_crs = source.crs_wkt or source.crs
        if not source_crs:
            raise RuntimeError(f"source layer has no CRS: {path}")
        source_bbox = _bbox_in_crs(CONTEXTS[archive.region], source_crs)
        for raw in source.filter(bbox=source_bbox):
            geometry = raw.get("geometry")
            if not geometry:
                continue
            geometry = transform_geom(source_crs, "EPSG:4326", geometry, antimeridian_cutting=True)
            if hasattr(geometry, "__geo_interface__"):
                geometry = dict(geometry.__geo_interface__)
            properties = {key: _json_value(value) for key, value in dict(raw["properties"]).items()}
            properties.update(
                {
                    "terrai_dataset_id": dataset.dataset_id,
                    "terrai_region": archive.region,
                    "terrai_source_layer": path.stem,
                    "terrai_source_archive": Path(archive.url).name,
                    "terrai_source_updated_at": dataset.source_updated_at,
                    "terrai_retrieved_at": retrieved_at,
                    "terrai_source_url": archive.url,
                }
            )
            yield {"type": "Feature", "geometry": geometry, "properties": properties}


def build(*, output: Path = OUTPUT) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    retrieved_at = utc_timestamp()
    manifest: dict[str, Any] = {"retrieved_at": retrieved_at, "scope": SCOPE, "datasets": {}}
    with tempfile.TemporaryDirectory(prefix="terrai-mlit-wide-") as temporary:
        temp = Path(temporary)
        for dataset in WIDE_DATASETS:
            downloads = []
            collection = StreamedCollection(
                output / dataset.output,
                dataset.dataset_id,
                {
                    "source_updated_at": dataset.source_updated_at,
                    "retrieved_at": retrieved_at,
                    "license": dataset.license,
                    "scope": SCOPE,
                },
            )
            try:
                for index, archive in enumerate(dataset.archives):
                    archive_path = temp / f"{dataset.dataset_id}-{index}.zip"
                    result = download_file(archive.url, archive_path, timeout=300)
                    extracted = temp / f"{dataset.dataset_id}-{index}"
                    extracted.mkdir()
                    safe_extract_zip(archive_path, extracted)
                    layers = _layers(extracted, dataset.include)
                    if not layers:
                        raise RuntimeError(f"no supported layers in {archive.url}")
                    for layer in layers:
                        for feature in _iter_features(layer, dataset, archive, retrieved_at):
                            collection.add(feature)
                    downloads.append(
                        {
                            "url": archive.url,
                            "region": archive.region,
                            "sha256": result["sha256"],
                            "last_modified": result["http_last_modified"],
                            "layers": len(layers),
                        }
                    )
                    # One archive's footprint at a time: ~330 MB of zips total.
                    archive_path.unlink()
                    shutil.rmtree(extracted)
            except BaseException:
                collection.discard()
                raise
            collection.close()
            manifest["datasets"][dataset.key] = {
                "dataset_id": dataset.dataset_id,
                "output": f"data/external/mlit_wide/{dataset.output}",
                "source_updated_at": dataset.source_updated_at,
                "retrieved_at": retrieved_at,
                "license": dataset.license,
                "feature_count": collection.count,
                "downloads": downloads,
            }
            print(f"[mlit-wide] {dataset.key}: {collection.count} features", flush=True)
    write_json_atomic(output / "metadata.json", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="accepted for data-task compatibility")
    parser.parse_args()
    manifest = build()
    counts = ", ".join(f"{key}={row['feature_count']}" for key, row in manifest["datasets"].items())
    print(f"Wrote wide MLIT subsets: {counts}")


if __name__ == "__main__":
    main()
