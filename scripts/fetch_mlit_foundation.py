"""Download and spatially subset open MLIT foundation datasets for Kanto.

Raw archives are intentionally temporary. The products under ``data/mlit`` are
a gitignored reproducible acquisition — one scope, the mainland-Kanto window
(Tokyo, Kanagawa, Chiba, Saitama) — with provenance on every feature. Outputs
stream one feature at a time because the land-use mesh alone is on the order
of two million features (docs/refactor/kanto-foundation-coverage/00-overview.md).
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterator

import fiona
from fiona.transform import transform, transform_geom

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from terrai_spatial.pipeline.http import download_file  # noqa: E402
from terrai_spatial.pipeline.io import safe_extract_zip, serialize_json, write_json_atomic  # noqa: E402
from terrai_spatial.pipeline.provenance import utc_timestamp  # noqa: E402
from terrai_spatial.pipeline.regions import MLIT_ACQUISITION_BOUNDS  # noqa: E402

OUTPUT = ROOT / "data/mlit"
CONTEXTS = MLIT_ACQUISITION_BOUNDS
SCOPE = "TerrAI Kanto acquisition: mainland Tokyo, Kanagawa, Chiba and Saitama"

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


@dataclass(frozen=True)
class Archive:
    url: str
    region: str


@dataclass(frozen=True)
class Dataset:
    key: str
    dataset_id: str
    output: str
    source_updated_at: str
    license: str
    archives: tuple[Archive, ...]
    include: str = "preferred"


KSJ = "https://nlftp.mlit.go.jp/ksj/gml/data"
KOKJO = "https://nlftp.mlit.go.jp/kokjo"
LAND_HISTORY_ROOT = f"{KOKJO}/inspect/landclassification/land/land_history_2011/mapdata"


def _per_prefecture(template: str) -> tuple[Archive, ...]:
    return tuple(Archive(template.format(code=code), "kanto") for code in PREFECTURES)


DATASETS = (
    Dataset(
        "landClassification50k", "kokjo-land-classification-50k", "land_classification_50k.geojson",
        "current download; map-sheet vintage varies", "Public Data License 1.0; Survey Act and redistribution cautions apply",
        tuple(Archive(f"{KOKJO}/tochimizu/F3/GIS/{sheet}.zip", "kanto") for sheet in F3_SHEETS),
        "all_polygon_shapefiles",
    ),
    Dataset(
        "floodHistory", "kokjo-all-period-flood-history", "flood_history.geojson", "2025-03",
        "Public Data License 1.0; attribution/edit notice and redistribution cautions apply",
        (Archive(f"{KOKJO}/tochimizu/FC/GIS/1896_2019_sinsui_add24.zip", "kanto"),), "all_shapefiles",
    ),
    Dataset(
        "landHistory", "kokjo-land-history-gis", "land_history.geojson", "2011 survey package",
        "Public Data License 1.0; Survey Act and redistribution cautions apply",
        tuple(Archive(f"{LAND_HISTORY_ROOT}/{sheet}/{sheet}_gisdata.zip", "kanto") for sheet in LAND_HISTORY_SHEETS),
        "all_shapefiles",
    ),
    Dataset(
        "landslideWarning", "ksj-a33-2025", "landslide_warning.geojson", "2025-08-01",
        "CC BY 4.0 with provider-specific partial restrictions",
        _per_prefecture(f"{KSJ}/A33/A33-25/A33-25_{{code}}_GEOJSON.zip"),
    ),
    Dataset(
        "multistageFlood", "ksj-a53-2025", "multistage_flood.geojson", "2025 release",
        "CC BY 4.0",
        (Archive(f"{KSJ}/A53/A53-25/A53-25_83_GEOJSON.zip", "kanto"),), "all_geojson",
    ),
    Dataset(
        "publishedLandPrice", "ksj-l01-2026", "published_land_price.geojson", "2026-01-01",
        "CC BY 4.0",
        _per_prefecture(f"{KSJ}/L01/L01-26/L01-26_{{code}}_GML.zip"),
    ),
    Dataset(
        "embankmentRegulation", "ksj-a56-2025", "embankment_regulation.geojson", "2025-07-18",
        "CC BY 4.0; regulatory boundaries must not be modified",
        _per_prefecture(f"{KSJ}/A56/A56-25/A56-25_{{code}}_GML.zip"),
    ),
    Dataset(
        "railway", "ksj-n02-2025", "railway.geojson", "2025-12-31", "CC BY 4.0",
        (Archive(f"{KSJ}/N02/N02-25/N02-25_GML.zip", "kanto"),), "utf8_geojson",
    ),
    # Primary mesh 5238 is clipped to Kanagawa's Hakone-west sliver instead of
    # ingesting a block of Shizuoka; every other sheet uses the Kanto window.
    Dataset(
        "landUseMesh", "ksj-l03b-2021", "land_use_mesh.geojson", "2021",
        "Public Data License 1.0",
        tuple(
            Archive(f"{KSJ}/L03-b/L03-b-21/L03-b-21_{mesh}-jgd2011_GML.zip", "hakone_west" if mesh == "5238" else "kanto")
            for mesh in LAND_USE_MESHES
        ),
        "all_shapefiles",
    ),
    Dataset(
        "prefecturalLandPrice", "ksj-l02-2025", "prefectural_land_price.geojson", "2025-07-01",
        "CC BY 4.0",
        _per_prefecture(f"{KSJ}/L02/L02-25/L02-25_{{code}}_GML.zip"),
    ),
)


def _layers(root: Path, mode: str) -> list[Path]:
    geojson = sorted(root.rglob("*.geojson"))
    shapes = sorted(root.rglob("*.shp"))
    if mode == "all_geojson":
        return geojson
    if mode == "utf8_geojson":
        return [path for path in geojson if "UTF-8" in path.parts]
    if mode == "all_shapefiles":
        return shapes
    if mode == "all_polygon_shapefiles":
        return [path for path in shapes if path.name.startswith("PL_")]
    return geojson or shapes


def _json_value(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _bbox_in_crs(
    bbox: tuple[float, float, float, float],
    target_crs: Any,
) -> tuple[float, float, float, float]:
    """Transform all WGS84 bbox corners before source-side filtering."""
    min_x, min_y, max_x, max_y = bbox
    xs, ys = transform(
        "EPSG:4326",
        target_crs,
        [min_x, min_x, max_x, max_x],
        [min_y, max_y, min_y, max_y],
    )
    return min(xs), min(ys), max(xs), max(ys)


class StreamedCollection:
    """A compact FeatureCollection written feature-by-feature, atomically.

    Byte-compatible with ``write_json_atomic(compact=True,
    trailing_newline=False)`` for the same envelope and features, without ever
    holding more than one feature in memory.
    """

    def __init__(self, path: Path, name: str, metadata: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._path = path
        # A unique temporary name per writer, like the atomic writers in
        # pipeline.io: concurrent builds must never interleave into one
        # temp file and publish garbage through the final rename.
        handle = tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=path.parent, prefix=path.name + ".", suffix=".part", delete=False
        )
        self._temporary = Path(handle.name)
        self._handle = handle
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
    with tempfile.TemporaryDirectory(prefix="terrai-mlit-") as temporary:
        temp = Path(temporary)
        for dataset in DATASETS:
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
                "output": f"data/mlit/{dataset.output}",
                "source_updated_at": dataset.source_updated_at,
                "retrieved_at": retrieved_at,
                "license": dataset.license,
                "feature_count": collection.count,
                "downloads": downloads,
            }
            print(f"[mlit] {dataset.key}: {collection.count} features", flush=True)
    write_json_atomic(output / "metadata.json", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="accepted for data-task compatibility")
    parser.parse_args()
    manifest = build()
    counts = ", ".join(f"{key}={row['feature_count']}" for key, row in manifest["datasets"].items())
    print(f"Wrote open MLIT subsets: {counts}")


if __name__ == "__main__":
    main()
