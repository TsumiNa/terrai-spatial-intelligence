#!/usr/bin/env python3
"""Fetch small, analysis-ready AlphaEarth Satellite Embedding crops.

The source is the public Source Cooperative mirror of Google's annual
Satellite Embedding V1 COGs.  The script reads only COG byte ranges needed for
the two TerrAI demo bounds; it never downloads a global tile in full.

Runtime (kept outside the static demo):
  uv run --with rasterio --with pyproj --with pillow \
    python scripts/fetch_google_satellite_embedding.py
"""

from __future__ import annotations

import math
import re
import sys
import tempfile
import urllib.parse
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import rasterio
from PIL import Image
from pyproj import Transformer
from rasterio.windows import from_bounds

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from terrai_spatial.pipeline.http import download_bytes  # noqa: E402
from terrai_spatial.pipeline.io import write_json_atomic  # noqa: E402
from terrai_spatial.pipeline.regions import STUDY_BOUNDS  # noqa: E402

OUT = ROOT / "data" / "google" / "satellite_embedding"
S3_BUCKET = "us-west-2.opendata.source.coop"
S3_ENDPOINT = "https://s3.us-west-2.amazonaws.com"
PREFIX = "tge-labs/aef/v1/annual"
YEARS = (2023, 2024)
ZONE = "54N"
NODATA = -128
DOWNLOAD_TIMEOUT = 45

REGIONS = {
    "yokohama": {"label": "横滨 · 保土谷区", "bounds": STUDY_BOUNDS["yokohama"]},
    "mobara": {"label": "千叶 · 茂原市", "bounds": STUDY_BOUNDS["mobara"]},
}


def list_vrts(year: int) -> list[str]:
    prefix = f"{PREFIX}/{year}/{ZONE}/"
    query = urllib.parse.urlencode({"list-type": "2", "prefix": prefix, "max-keys": "1000"})
    root = ET.fromstring(download_bytes(f"{S3_ENDPOINT}/{S3_BUCKET}?{query}", timeout=DOWNLOAD_TIMEOUT))
    namespace = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}
    keys = [
        item.find("s3:Key", namespace).text
        for item in root.findall("s3:Contents", namespace)
        if item.find("s3:Key", namespace).text.endswith(".vrt")
    ]
    if not keys:
        raise RuntimeError(f"No VRT files found for {year}/{ZONE}")
    return keys


def vrt_url(key: str) -> str:
    return f"{S3_ENDPOINT}/{S3_BUCKET}/{key}"


def parse_vrt_extent(xml: bytes) -> tuple[float, float, float, float]:
    text = xml.decode("utf-8")
    size_match = re.search(r'<VRTDataset rasterXSize="(\d+)" rasterYSize="(\d+)"', text)
    transform_match = re.search(r"<GeoTransform>\s*([^<]+)</GeoTransform>", text)
    if not size_match or not transform_match:
        raise ValueError("VRT lacks raster size or GeoTransform")
    width, height = map(int, size_match.groups())
    x0, dx, _, y0, _, dy = [float(value) for value in transform_match.group(1).split(",")]
    x1, y1 = x0 + width * dx, y0 + height * dy
    return min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)


def locate_vrts(year: int, points_utm: dict[str, tuple[float, float]]) -> dict[str, tuple[str, bytes]]:
    keys = list_vrts(year)
    matches: dict[str, tuple[str, bytes]] = {}

    def fetch(key: str) -> tuple[str, bytes]:
        return key, download_bytes(vrt_url(key), timeout=DOWNLOAD_TIMEOUT)

    with ThreadPoolExecutor(max_workers=18) as executor:
        futures = [executor.submit(fetch, key) for key in keys]
        for future in as_completed(futures):
            key, xml = future.result()
            west, south, east, north = parse_vrt_extent(xml)
            for region, (x, y) in points_utm.items():
                if region not in matches and west <= x <= east and south <= y <= north:
                    matches[region] = (key, xml)
            if len(matches) == len(points_utm):
                for pending in futures:
                    pending.cancel()
                break
    missing = sorted(set(points_utm) - set(matches))
    if missing:
        raise RuntimeError(f"No embedding VRT found for {year}: {', '.join(missing)}")
    return matches


def localize_vrt(xml: bytes, key: str, directory: Path) -> Path:
    text = xml.decode("utf-8")
    tiff_key = key.removesuffix(".vrt") + ".tiff"
    source = f"/vsicurl/{S3_ENDPOINT}/{S3_BUCKET}/{tiff_key}"
    text = re.sub(
        r'<SourceDataset relativeToVRT="0">[^<]+</SourceDataset>',
        f'<SourceDataset relativeToVRT="0">{source}</SourceDataset>',
        text,
        count=1,
    )
    path = directory / Path(key).name
    path.write_text(text, encoding="utf-8")
    return path


def crop_embedding(vrt_path: Path, bounds_wgs84: tuple[float, float, float, float]) -> tuple[np.ndarray, rasterio.Affine]:
    to_utm = Transformer.from_crs("EPSG:4326", "EPSG:32654", always_xy=True)
    west, south, east, north = bounds_wgs84
    west_u, south_u = to_utm.transform(west, south)
    east_u, north_u = to_utm.transform(east, north)
    env = {
        "GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR",
        "CPL_VSIL_CURL_ALLOWED_EXTENSIONS": ".tiff,.vrt",
        "GDAL_HTTP_MULTIRANGE": "YES",
        "GDAL_HTTP_MERGE_CONSECUTIVE_RANGES": "YES",
    }
    with rasterio.Env(**env), rasterio.open(vrt_path) as dataset:
        window = from_bounds(west_u, south_u, east_u, north_u, dataset.transform)
        window = window.round_offsets().round_lengths()
        raw = dataset.read(window=window)
        transform = dataset.window_transform(window)
    values = np.moveaxis(raw, 0, -1).astype(np.float32)
    valid = np.all(values != NODATA, axis=-1)
    dequantized = ((values / 127.5) ** 2) * np.sign(values)
    dequantized[~valid] = np.nan
    norms = np.linalg.norm(dequantized, axis=-1, keepdims=True)
    dequantized = np.divide(dequantized, norms, out=np.full_like(dequantized, np.nan), where=norms > 0)
    return dequantized, transform


def percentile_scale(values: np.ndarray, valid: np.ndarray, low: float = 2, high: float = 98) -> np.ndarray:
    sample = values[valid]
    if sample.size == 0:
        return np.zeros(values.shape, dtype=np.float32)
    lo, hi = np.nanpercentile(sample, [low, high])
    if math.isclose(float(lo), float(hi)):
        return np.zeros(values.shape, dtype=np.float32)
    return np.clip((values - lo) / (hi - lo), 0, 1)


def change_rgb(change: np.ndarray, valid: np.ndarray) -> np.ndarray:
    scaled = percentile_scale(change, valid, 5, 99)
    stops = np.array([[21, 59, 48], [120, 166, 93], [232, 193, 79], [214, 91, 76]], dtype=float)
    position = scaled * (len(stops) - 1)
    index = np.floor(position).astype(int)
    index = np.clip(index, 0, len(stops) - 2)
    fraction = (position - index)[..., None]
    rgb = stops[index] * (1 - fraction) + stops[index + 1] * fraction
    rgba = np.zeros((*change.shape, 4), dtype=np.uint8)
    rgba[..., :3] = rgb.astype(np.uint8)
    rgba[..., 3] = np.where(valid, 215, 0).astype(np.uint8)
    return rgba


def latent_rgb(embedding: np.ndarray, valid: np.ndarray, basis: np.ndarray, mean: np.ndarray) -> np.ndarray:
    projected = np.full((*embedding.shape[:2], 3), np.nan, dtype=np.float32)
    projected[valid] = (embedding[valid] - mean) @ basis
    rgb = np.zeros_like(projected)
    for channel in range(3):
        rgb[..., channel] = percentile_scale(projected[..., channel], valid, 2, 98)
    rgba = np.zeros((*embedding.shape[:2], 4), dtype=np.uint8)
    rgba[..., :3] = (rgb * 255).astype(np.uint8)
    rgba[..., 3] = np.where(valid, 205, 0).astype(np.uint8)
    return rgba


def geo_bounds(transform: rasterio.Affine, shape: tuple[int, int]) -> list[list[float]]:
    height, width = shape
    to_wgs = Transformer.from_crs("EPSG:32654", "EPSG:4326", always_xy=True)
    west, north = transform * (0, 0)
    east, south = transform * (width, height)
    west_lon, south_lat = to_wgs.transform(west, south)
    east_lon, north_lat = to_wgs.transform(east, north)
    return [[south_lat, west_lon], [north_lat, east_lon]]


def block_features(
    region: str,
    change: np.ndarray,
    embedding: np.ndarray,
    valid: np.ndarray,
    transform: rasterio.Affine,
    block: int = 10,
) -> list[dict]:
    height, width = change.shape
    to_wgs = Transformer.from_crs("EPSG:32654", "EPSG:4326", always_xy=True)
    global_valid = change[valid]
    p95 = float(np.nanpercentile(global_valid, 95)) if global_valid.size else 1.0
    features = []
    row_id = 0
    for row in range(0, height, block):
        for col in range(0, width, block):
            row_end, col_end = min(row + block, height), min(col + block, width)
            mask = valid[row:row_end, col:col_end]
            support = int(mask.sum())
            total = mask.size
            if support < max(4, total * 0.25):
                continue
            block_change = change[row:row_end, col:col_end][mask]
            block_embedding = embedding[row:row_end, col:col_end][mask]
            mean_embedding = np.nanmean(block_embedding, axis=0)
            mean_embedding /= max(float(np.linalg.norm(mean_embedding)), 1e-9)
            value = float(np.nanmean(block_change))
            score = int(round(100 * min(value / max(p95, 1e-9), 1)))
            west_u, north_u = transform * (col, row)
            east_u, south_u = transform * (col_end, row_end)
            west, south = to_wgs.transform(west_u, south_u)
            east, north = to_wgs.transform(east_u, north_u)
            row_id += 1
            features.append(
                {
                    "type": "Feature",
                    "id": f"{region}-aef-{row_id:03d}",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[west, south], [east, south], [east, north], [west, north], [west, south]]],
                    },
                    "properties": {
                        "region": region,
                        "cell_id": f"AEF-{row_id:03d}",
                        "change_score": score,
                        "cosine_change": round(value, 5),
                        "valid_pixels": support,
                        "support_pct": round(100 * support / total),
                        "evidence_status": "observed_embedding",
                        "year_pair": "2023→2024",
                        "embedding_preview": [round(float(item), 4) for item in mean_embedding[:8]],
                    },
                }
            )
    return features


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    to_utm = Transformer.from_crs("EPSG:4326", "EPSG:32654", always_xy=True)
    centers = {
        key: to_utm.transform((value["bounds"][0] + value["bounds"][2]) / 2, (value["bounds"][1] + value["bounds"][3]) / 2)
        for key, value in REGIONS.items()
    }

    crops: dict[tuple[str, int], tuple[np.ndarray, rasterio.Affine, str]] = {}
    with tempfile.TemporaryDirectory(prefix="terrai-aef-") as temporary:
        temporary_path = Path(temporary)
        for year in YEARS:
            located = locate_vrts(year, centers)
            for region, (key, xml) in located.items():
                local_vrt = localize_vrt(xml, key, temporary_path)
                crop, transform = crop_embedding(local_vrt, REGIONS[region]["bounds"])
                crops[(region, year)] = (crop, transform, key)

    samples = []
    for region in REGIONS:
        embedding = crops[(region, 2024)][0]
        valid = np.all(np.isfinite(embedding), axis=-1)
        samples.append(embedding[valid][:: max(1, int(valid.sum() / 6000))])
    sample = np.concatenate(samples, axis=0)
    mean = np.mean(sample, axis=0)
    _, _, vh = np.linalg.svd(sample - mean, full_matrices=False)
    basis = vh[:3].T

    all_features = []
    overlays = {}
    summaries = {}
    for region in REGIONS:
        previous, transform, key_2023 = crops[(region, 2023)]
        current, transform_2024, key_2024 = crops[(region, 2024)]
        if previous.shape != current.shape or transform != transform_2024:
            raise RuntimeError(f"Year crops do not align for {region}")
        valid = np.all(np.isfinite(previous), axis=-1) & np.all(np.isfinite(current), axis=-1)
        change = 1 - np.einsum("ijk,ijk->ij", previous, current)
        change[~valid] = np.nan

        change_path = OUT / f"{region}_change_2023_2024.png"
        latent_path = OUT / f"{region}_latent_2024.png"
        Image.fromarray(change_rgb(change, valid), "RGBA").save(change_path)
        Image.fromarray(latent_rgb(current, valid, basis, mean), "RGBA").save(latent_path)
        bounds = geo_bounds(transform, change.shape)
        overlays[region] = {
            "bounds": bounds,
            "change_image": str(change_path.relative_to(ROOT)),
            "latent_image": str(latent_path.relative_to(ROOT)),
        }
        values = change[valid]
        summaries[region] = {
            "label": REGIONS[region]["label"],
            "pixel_count": int(valid.sum()),
            "valid_pct": round(100 * float(valid.mean()), 1),
            "mean_cosine_change": round(float(np.nanmean(values)), 5),
            "p95_cosine_change": round(float(np.nanpercentile(values, 95)), 5),
            "source_vrt_2023": key_2023,
            "source_vrt_2024": key_2024,
        }
        all_features.extend(block_features(region, change, current, valid, transform))

    write_json_atomic(
        OUT / "embedding_evidence.geojson",
        {"type": "FeatureCollection", "features": all_features},
    )
    write_json_atomic(
        OUT / "summary.json",
        {
            "generated_at": "2026-07-20",
            "dataset": "Google Satellite Embedding V1 / AlphaEarth Foundations",
            "license": "CC BY 4.0",
            "attribution": "The AlphaEarth Foundations Satellite Embedding dataset is produced by Google and Google DeepMind.",
            "years": list(YEARS),
            "role": "Annual change evidence and similarity features; excluded from suitability scores until local validation.",
            "source": "Source Cooperative public mirror (not officially supported by Google)",
            "overlays": overlays,
            "regions": summaries,
        },
    )
    print(f"Wrote {len(all_features)} evidence cells to {OUT}")


if __name__ == "__main__":
    main()
