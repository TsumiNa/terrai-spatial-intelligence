"""Download and spatially subset open MLIT foundation datasets.

Raw archives are intentionally temporary.  The committed products contain only
the two TerrAI demonstration contexts, plus provenance on every feature.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

import fiona
from fiona.transform import transform, transform_geom

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from terrai_spatial.pipeline.http import download_file  # noqa: E402
from terrai_spatial.pipeline.io import safe_extract_zip, write_json_atomic  # noqa: E402
from terrai_spatial.pipeline.provenance import utc_timestamp  # noqa: E402
from terrai_spatial.pipeline.regions import MLIT_CONTEXT_BOUNDS  # noqa: E402

OUTPUT = ROOT / "data/mlit"
CONTEXTS = MLIT_CONTEXT_BOUNDS


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
DATASETS = (
    Dataset(
        "landClassification50k", "kokjo-land-classification-50k", "land_classification_50k.geojson",
        "current download; map-sheet vintage varies", "Public Data License 1.0; Survey Act and redistribution cautions apply",
        (Archive(f"{KOKJO}/tochimizu/F3/GIS/Yokohama.zip", "yokohama"), Archive(f"{KOKJO}/tochimizu/F3/GIS/Chiba.zip", "mobara")),
        "all_polygon_shapefiles",
    ),
    Dataset(
        "floodHistory", "kokjo-all-period-flood-history", "flood_history.geojson", "2025-03",
        "Public Data License 1.0; attribution/edit notice and redistribution cautions apply",
        (Archive(f"{KOKJO}/tochimizu/FC/GIS/1896_2019_sinsui_add24.zip", "both"),), "all_shapefiles",
    ),
    Dataset(
        "landHistory", "kokjo-land-history-gis", "land_history.geojson", "2011 survey package",
        "Public Data License 1.0; Survey Act and redistribution cautions apply",
        (Archive(f"{KOKJO}/inspect/landclassification/land/land_history_2011/mapdata/533904/533904_gisdata.zip", "yokohama"), Archive(f"{KOKJO}/inspect/landclassification/land/land_history_2011/mapdata/534020/534020_gisdata.zip", "mobara")),
        "all_shapefiles",
    ),
    Dataset(
        "landslideWarning", "ksj-a33-2025", "landslide_warning.geojson", "2025-08-01",
        "CC BY 4.0 with provider-specific partial restrictions",
        (Archive(f"{KSJ}/A33/A33-25/A33-25_14_GEOJSON.zip", "yokohama"), Archive(f"{KSJ}/A33/A33-25/A33-25_12_GEOJSON.zip", "mobara")),
    ),
    Dataset(
        "multistageFlood", "ksj-a53-2025", "multistage_flood.geojson", "2025 release",
        "CC BY 4.0",
        (Archive(f"{KSJ}/A53/A53-25/A53-25_83_GEOJSON.zip", "both"),), "all_geojson",
    ),
    Dataset(
        "publishedLandPrice", "ksj-l01-2026", "published_land_price.geojson", "2026-01-01",
        "CC BY 4.0",
        (Archive(f"{KSJ}/L01/L01-26/L01-26_14_GML.zip", "yokohama"), Archive(f"{KSJ}/L01/L01-26/L01-26_12_GML.zip", "mobara")),
    ),
    Dataset(
        "embankmentRegulation", "ksj-a56-2025", "embankment_regulation.geojson", "2025-07-18",
        "CC BY 4.0; regulatory boundaries must not be modified",
        (Archive(f"{KSJ}/A56/A56-25/A56-25_14_GML.zip", "yokohama"), Archive(f"{KSJ}/A56/A56-25/A56-25_12_GML.zip", "mobara")),
    ),
    Dataset(
        "railway", "ksj-n02-2025", "railway.geojson", "2025-12-31", "CC BY 4.0",
        (Archive(f"{KSJ}/N02/N02-25/N02-25_GML.zip", "both"),), "utf8_geojson",
    ),
    Dataset(
        "landUseMesh", "ksj-l03b-2021", "land_use_mesh.geojson", "2021",
        "Public Data License 1.0",
        (Archive(f"{KSJ}/L03-b/L03-b-21/L03-b-21_5339-jgd2011_GML.zip", "yokohama"), Archive(f"{KSJ}/L03-b/L03-b-21/L03-b-21_5340-jgd2011_GML.zip", "mobara")),
        "all_shapefiles",
    ),
    Dataset(
        "prefecturalLandPrice", "ksj-l02-2025", "prefectural_land_price.geojson", "2025-07-01",
        "CC BY 4.0",
        (Archive(f"{KSJ}/L02/L02-25/L02-25_14_GML.zip", "yokohama"), Archive(f"{KSJ}/L02/L02-25/L02-25_12_GML.zip", "mobara")),
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


def _target_contexts(region: str) -> Iterable[tuple[str, tuple[float, float, float, float]]]:
    return CONTEXTS.items() if region == "both" else ((region, CONTEXTS[region]),)


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


def _read_features(path: Path, dataset: Dataset, archive: Archive, retrieved_at: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with fiona.open(path) as source:
        source_crs = source.crs_wkt or source.crs
        if not source_crs:
            raise RuntimeError(f"source layer has no CRS: {path}")
        for region, bbox in _target_contexts(archive.region):
            source_bbox = _bbox_in_crs(bbox, source_crs)
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
                        "terrai_region": region,
                        "terrai_source_layer": path.stem,
                        "terrai_source_archive": Path(archive.url).name,
                        "terrai_source_updated_at": dataset.source_updated_at,
                        "terrai_retrieved_at": retrieved_at,
                        "terrai_source_url": archive.url,
                    }
                )
                rows.append({"type": "Feature", "geometry": geometry, "properties": properties})
    return rows


def build(*, output: Path = OUTPUT) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    retrieved_at = utc_timestamp()
    manifest: dict[str, Any] = {"retrieved_at": retrieved_at, "datasets": {}}
    with tempfile.TemporaryDirectory(prefix="terrai-mlit-") as temporary:
        temp = Path(temporary)
        for dataset in DATASETS:
            features: list[dict[str, Any]] = []
            downloads = []
            for index, archive in enumerate(dataset.archives):
                archive_path = temp / f"{dataset.dataset_id}-{index}.zip"
                result = download_file(archive.url, archive_path, timeout=120)
                details = {"sha256": result["sha256"], "last_modified": result["http_last_modified"]}
                extracted = temp / f"{dataset.dataset_id}-{index}"
                extracted.mkdir()
                safe_extract_zip(archive_path, extracted)
                layers = _layers(extracted, dataset.include)
                if not layers:
                    raise RuntimeError(f"no supported layers in {archive.url}")
                for layer in layers:
                    features.extend(_read_features(layer, dataset, archive, retrieved_at))
                downloads.append({"url": archive.url, "region": archive.region, **details, "layers": len(layers)})
            collection = {
                "type": "FeatureCollection",
                "name": dataset.dataset_id,
                "metadata": {
                    "source_updated_at": dataset.source_updated_at,
                    "retrieved_at": retrieved_at,
                    "license": dataset.license,
                    "scope": "TerrAI Yokohama and Mobara demonstration contexts",
                },
                "features": features,
            }
            write_json_atomic(output / dataset.output, collection, compact=True, trailing_newline=False)
            manifest["datasets"][dataset.key] = {
                "dataset_id": dataset.dataset_id,
                "output": f"data/mlit/{dataset.output}",
                "source_updated_at": dataset.source_updated_at,
                "retrieved_at": retrieved_at,
                "license": dataset.license,
                "feature_count": len(features),
                "downloads": downloads,
            }
    write_json_atomic(output / "metadata.json", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="accepted for data-task compatibility")
    parser.parse_args()
    manifest = build()
    counts = ", ".join(f"{key}={row['feature_count']}" for key, row in manifest["datasets"].items())
    print(f"Wrote open MLIT subsets: {counts}")


if __name__ == "__main__":
    main()
