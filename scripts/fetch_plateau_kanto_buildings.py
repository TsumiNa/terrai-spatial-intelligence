"""Acquire PLATEAU LOD1 building heights for mainland Kanto.

The merged basemap tiles (docs/refactor/osm-basemap-tiles/) extrude buildings in
2.5D by a baked height; where a municipality is modelled by Project PLATEAU, that
height should be the **measured** one, not an estimate. PLATEAU publishes LOD1
building models per municipality as CityGML carrying ``bldg:measuredHeight``
(https://www.mlit.go.jp/plateau/, Site Policy §3: attribution, commercial OK).

This task reads the pinned per-municipality CityGML resources (source_manifest.json,
frozen from the geospatial.jp CKAN so catalog drift fails visibly) and distils each
building to one point + its measured height — all the downstream merge needs to
join height onto a footprint. It processes one municipality at a time, streaming
``bldg`` GML **directly out of the downloaded zip** (no disk extraction) and
deleting the archive after, so peak disk stays at one archive, not tens of GB.

Output: ``data/plateau/kanto_buildings/heights.geojson`` — a FeatureCollection of
Points, each ``{"height": <m>, "plateau_id": <gml:id>, "municipality": <code>}``.
The merge (merge_kanto_buildings.py) builds an STRtree of these and assigns a
building's height from the PLATEAU point inside its footprint (height_source
``plateau``), else OSM tags, else a class estimate.

CityGML is parsed with the stdlib reader and local-name matching (namespace-agnostic
across CityGML 1.0/2.0 and the FGD-like gml versions), the same approach the FGD
task uses. posLists are ``lat lon z …`` (JGD2011 geographic + altitude); each
building's representative point is its lod0FootPrint (else lod1Solid) centroid.
"""

from __future__ import annotations

import argparse
import re
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Iterator
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.fetch_mlit_foundation import StreamedCollection  # noqa: E402
from terrai_spatial.pipeline.http import download_file  # noqa: E402
from terrai_spatial.pipeline.io import read_json_object, write_json_atomic  # noqa: E402
from terrai_spatial.pipeline.provenance import utc_timestamp  # noqa: E402

OUTPUT = ROOT / "data/plateau/kanto_buildings"
DATASET_ID = "plateau-kanto-buildings"
LICENSE = "PLATEAU Site Policy §3 (国土交通省) — attribution, commercial use permitted"
ATTRIBUTION = "3D都市モデル（Project PLATEAU）国土交通省"
SCOPE = "TerrAI Kanto acquisition: PLATEAU LOD1 measured building heights for the 2.5D extrusion"
_BLDG_MEMBER = re.compile(r"udx/bldg/.*\.gml$", re.IGNORECASE)


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _gml_id(element: ElementTree.Element) -> str | None:
    for key, value in element.attrib.items():
        if _local(key) == "id":
            return value
    return None


def _footprint_point(building: ElementTree.Element) -> tuple[float, float] | None:
    """A representative [lon, lat] inside a building's ground geometry.

    The **mean of the footprint's vertices** — a cheap interior point, not the
    area-weighted polygon centroid, which is all the point-in-footprint height
    join needs. Prefers ``lod0FootPrint`` (a flat 2D footprint), falling back to
    ``lod1Solid``. CityGML posLists are ``lat lon z …`` triples, so every third
    value (altitude) is dropped and the lat/lon pair averaged.
    """

    footprint: ElementTree.Element | None = None
    solid: ElementTree.Element | None = None
    for node in building.iter():
        name = _local(node.tag)
        if name == "lod0FootPrint" and footprint is None:
            footprint = node
        elif name == "lod1Solid" and solid is None:
            solid = node
    source = footprint if footprint is not None else solid
    if source is None:
        return None
    lon_sum = lat_sum = 0.0
    count = 0
    for node in source.iter():
        if _local(node.tag) != "posList" or not node.text:
            continue
        values = [float(v) for v in node.text.split()]
        for i in range(0, len(values) - 2, 3):
            lat_sum += values[i]
            lon_sum += values[i + 1]
            count += 1
    if count == 0:
        return None
    return lon_sum / count, lat_sum / count


def iter_building_heights(stream: Any, municipality: str) -> Iterator[dict[str, Any]]:
    """Yield a Point feature (centroid + measured height) per modelled building."""

    context = ElementTree.iterparse(stream, events=("start", "end"))
    _event, root = next(context)
    for event, element in context:
        if event != "end" or _local(element.tag) != "Building":
            continue
        height_text: str | None = None
        for node in element.iter():
            if _local(node.tag) == "measuredHeight" and node.text:
                height_text = node.text.strip()
                break
        if height_text is not None:
            try:
                height = float(height_text)
            except ValueError:
                height = None
            point = _footprint_point(element) if height and height > 0 else None
            if point is not None:
                yield {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [point[0], point[1]]},
                    "properties": {"height": height, "plateau_id": _gml_id(element), "municipality": municipality},
                }
        element.clear()
        root.clear()


def _read_source_manifest(output: Path) -> dict[str, Any]:
    return read_json_object(output / "source_manifest.json", label="PLATEAU source manifest")


def build(*, output: Path = OUTPUT, limit: int | None = None) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    retrieved_at = utc_timestamp()
    manifest = _read_source_manifest(output)
    selections = manifest.get("resources", [])
    if limit is not None:
        selections = selections[:limit]

    collection = StreamedCollection(
        output / "heights.geojson",
        DATASET_ID,
        {"retrieved_at": retrieved_at, "license": LICENSE, "scope": SCOPE, "attribution": ATTRIBUTION},
    )
    sources: list[dict[str, Any]] = []
    try:
        for selection in selections:
            code = selection["code"]
            with tempfile.TemporaryDirectory(prefix="terrai-plateau-") as temporary:
                archive = Path(temporary) / f"{selection['package']}.zip"
                result = download_file(selection["url"], archive, timeout=1800)
                count = 0
                with zipfile.ZipFile(archive) as bundle:
                    members = [name for name in bundle.namelist() if _BLDG_MEMBER.search(name)]
                    for member in members:
                        with bundle.open(member) as stream:
                            for feature in iter_building_heights(stream, code):
                                collection.add(feature)
                                count += 1
            sources.append(
                {
                    "code": code,
                    "prefecture": selection.get("prefecture", ""),
                    "package": selection["package"],
                    "year": selection.get("year"),
                    "sha256": result["sha256"],
                    "building_count": count,
                }
            )
    except BaseException:
        collection.discard()
        raise
    collection.close()

    product = output / "heights.geojson"
    try:
        product_path = str(product.relative_to(ROOT))
    except ValueError:
        product_path = str(product)
    out_manifest = {
        "retrieved_at": retrieved_at,
        "scope": SCOPE,
        "dataset_id": DATASET_ID,
        "output": product_path,
        "license": LICENSE,
        "attribution": ATTRIBUTION,
        "municipality_count": len(sources),
        "building_count": collection.count,
        "sources": sources,
    }
    write_json_atomic(output / "metadata.json", out_manifest)
    return out_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="accepted for data-task compatibility")
    parser.add_argument("--limit", type=int, default=None, help="process only the first N municipalities (spike)")
    args = parser.parse_args()
    manifest = build(limit=args.limit)
    print(
        f"Wrote PLATEAU Kanto heights: {manifest['building_count']} measured buildings "
        f"across {manifest['municipality_count']} municipalities"
    )


if __name__ == "__main__":
    main()
