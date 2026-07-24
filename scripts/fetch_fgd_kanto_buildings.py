"""Normalize pinned 基盤地図情報 (FGD) building outlines into Kanto footprints.

The self-built merged basemap tiles (docs/refactor/osm-basemap-tiles/00-overview.md)
need a government building layer to fill OSM's suburban and rural gaps. GSI's
基盤地図情報 「建築物の外周線」 is that layer: complete national coverage, and —
per docs/summary/government-3d-building-sources/ — 測量法 承認申請-exempt, usable
on attribution plus a processing note (加工表示). This task turns the pinned FGD
archive into one GeoJSON footprint layer, each feature tagged
``footprint_source: "fgd"`` with its FGD identifier, mirroring the OSM
acquisition (scripts/fetch_osm_kanto_buildings.py) so PR2's merge can lay OSM
over it and mint ``feature_id`` = ``fgd:<id>`` where the footprint is government.

Manual, registration-gated acquisition — reproduce the pinned input like this:

1. Register (free) at the Fundamental Geospatial Data download service,
   https://fgd.gsi.go.jp/download/ . Account creation and the authenticated
   download are a human step; this task never fetches over the network.
2. Select the product 「建築物の外周線」 (building outlines, feature type ``BldA``)
   for the four mainland-Kanto prefectures — Tokyo, Kanagawa, Chiba, Saitama —
   the same window as the OSM acquisition.
3. Download the JPGIS(GML) archive(s) and drop them, unmodified, into
   ``data/fgd/kanto_buildings/source/`` (nested per-mesh zips are fine — the task
   extracts one level of nesting; loose ``*.xml``/``*.gml`` are accepted too).
4. Record the publication vintage in
   ``data/fgd/kanto_buildings/source_manifest.json`` (``publication_vintage``).
5. Run ``uv run python scripts/fetch_fgd_kanto_buildings.py``. It writes the
   gitignored ``buildings.geojson`` product and the ``metadata.json`` manifest
   (feature count, per-archive sha256, vintage, licence); commit ``metadata.json``.

The FGD JPGIS GML flavour (custom ``FGD_GMLSchema`` namespace, GML 3.1.1/3.2
geometry) is parsed directly with the stdlib XML reader and local-name matching
rather than through OGR, whose FGD handling is inconsistent across builds; a
synthetic fixture in the test pins the parser to the documented schema.
"""

from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterator
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.fetch_mlit_foundation import StreamedCollection  # noqa: E402
from terrai_spatial.pipeline.io import (  # noqa: E402
    file_sha256,
    read_json_object,
    safe_extract_zip,
    write_json_atomic,
)
from terrai_spatial.pipeline.provenance import utc_timestamp  # noqa: E402
from terrai_spatial.pipeline.regions import MLIT_ACQUISITION_BOUNDS  # noqa: E402
from terrai_spatial.store import feature_bbox  # noqa: E402

SERVICE_URL = "https://fgd.gsi.go.jp/download/"
DATASET_BASE = "fgd-kanto-buildings"
OUTPUT = ROOT / "data/fgd/kanto_buildings"
# 承認申請-exempt basic-survey content; attribution + a processing note suffice.
LICENSE = "基盤地図情報 (GSI) — 測量法 承認申請-exempt; attribution + 加工表示 (processing note) required"
SCOPE = "TerrAI Kanto acquisition: 基盤地図情報 building outlines filling OSM's gaps inside the mainland window"
PREFECTURES = ("Tokyo", "Kanagawa", "Chiba", "Saitama")
WINDOW = MLIT_ACQUISITION_BOUNDS["kanto"]

# The FGD download packages 「建築物の外周線」 as ``BldA`` area features; the
# per-mesh files carry that token (romanized) in their name.
BUILDING_FEATURE = "BldA"
_MESH_RE = re.compile(r"FG-GML-([0-9]+(?:-[0-9]+)*)")


def _local(tag: str) -> str:
    """The local name of a namespaced XML tag (``{ns}Bld`` -> ``Bld``)."""

    return tag.rsplit("}", 1)[-1]


def _gml_id(element: ElementTree.Element) -> str | None:
    for key, value in element.attrib.items():
        if _local(key) == "id":
            return value
    return None


def _ring_from(element: ElementTree.Element) -> list[list[float]]:
    """Concatenate every ``gml:posList`` under ``element`` into one closed ring.

    FGD posLists are ``lat lon lat lon …`` (JGD2011 geographic, EPSG:6668, which
    equals WGS84 to sub-metre in Japan), so each pair is swapped to GeoJSON
    ``[lon, lat]``. A ring may be split across consecutive curve segments whose
    shared joint is repeated; that duplicate is dropped, and the ring is closed.
    """

    ring: list[list[float]] = []
    for node in element.iter():
        if _local(node.tag) != "posList" or not node.text:
            continue
        numbers = [float(value) for value in node.text.split()]
        segment = [[numbers[i + 1], numbers[i]] for i in range(0, len(numbers) - 1, 2)]
        if ring and segment and ring[-1] == segment[0]:
            segment = segment[1:]
        ring.extend(segment)
    if len(ring) >= 3 and ring[0] != ring[-1]:
        ring.append(ring[0])
    return ring


def parse_fgd_buildings(
    gml_path: Path,
) -> Iterator[tuple[str | None, str | None, str | None, dict[str, Any] | None]]:
    """Yield ``(gml_id, type, fid, geometry)`` for every ``BldA`` in one file."""

    # Retain the <Dataset> root and clear it after each feature: clearing only
    # the feature leaves processed siblings attached to the root, so memory would
    # grow with the mesh file's feature count.
    context = ElementTree.iterparse(gml_path, events=("start", "end"))
    _event, root = next(context)
    for event, element in context:
        if event != "end" or _local(element.tag) != BUILDING_FEATURE:
            continue
        type_text: str | None = None
        fid_text: str | None = None
        for child in element:
            name = _local(child.tag)
            if name == "type" and child.text:
                type_text = child.text.strip()
            elif name == "fid" and child.text:
                fid_text = child.text.strip()
        exterior: ElementTree.Element | None = None
        interiors: list[ElementTree.Element] = []
        for node in element.iter():
            name = _local(node.tag)
            if name == "exterior" and exterior is None:
                exterior = node
            elif name == "interior":
                interiors.append(node)
        rings: list[list[list[float]]] = []
        if exterior is not None:
            outer = _ring_from(exterior)
            if len(outer) >= 4:
                rings.append(outer)
        for interior in interiors:
            hole = _ring_from(interior)
            if len(hole) >= 4:
                rings.append(hole)
        geometry = {"type": "Polygon", "coordinates": rings} if rings else None
        yield _gml_id(element), type_text, fid_text, geometry
        element.clear()
        root.clear()


def _mesh_token(name: str) -> str:
    match = _MESH_RE.search(name)
    return match.group(1) if match else Path(name).stem


def _intersects_window(bbox: tuple[float, float, float, float]) -> bool:
    west, south, east, north = WINDOW
    return bbox[2] >= west and bbox[0] <= east and bbox[3] >= south and bbox[1] <= north


def iter_building_features(
    gml_files: list[Path],
    retrieved_at: str,
    source_updated_at: str,
    dataset_id: str,
    *,
    skipped: list[str] | None = None,
) -> Iterator[dict[str, Any]]:
    """Every FGD building outline touching the Kanto window, with provenance.

    The FGD identifier is the globally-unique feature id (``fid``) when the file
    carries one; otherwise the per-file ``gml:id`` is namespaced with its mesh
    code so it stays unique across the thousands of mesh files in one download.
    """

    for gml_path in gml_files:
        mesh = _mesh_token(gml_path.name)
        for gml_id, type_text, fid_text, geometry in parse_fgd_buildings(gml_path):
            if geometry is None:
                if skipped is not None:
                    skipped.append(fid_text or (f"{mesh}:{gml_id}" if gml_id else mesh))
                continue
            bbox = feature_bbox(geometry)
            if bbox is None or not _intersects_window(bbox):
                continue
            fgd_id = fid_text or (f"{mesh}:{gml_id}" if gml_id else mesh)
            properties: dict[str, Any] = {
                "fgd_id": fgd_id,
                "footprint_source": "fgd",
            }
            if type_text:
                properties["fgd_type"] = type_text
            if gml_id:
                properties["fgd_gml_id"] = gml_id
            properties.update(
                {
                    "terrai_dataset_id": dataset_id,
                    "terrai_region": "kanto",
                    "terrai_source_archive": gml_path.name,
                    "terrai_source_updated_at": source_updated_at,
                    "terrai_retrieved_at": retrieved_at,
                    "terrai_source_url": SERVICE_URL,
                }
            )
            yield {"type": "Feature", "geometry": geometry, "properties": properties}


def _is_building_gml(name: str) -> bool:
    return BUILDING_FEATURE in name or "建築物" in name


def collect_building_gml(source_dir: Path, workdir: Path) -> tuple[list[Path], list[dict[str, str]]]:
    """Extract the pinned archives and return the building GML files + sources.

    The user drops the FGD download (zip(s), possibly nesting per-mesh zips, or
    loose GML) into ``source_dir``; each dropped file is hashed for the manifest.
    Building files are selected by name (``BldA`` / 建築物); if none match, every
    GML is parsed and the reader keeps only its ``BldA`` features.
    """

    if not source_dir.is_dir():
        return [], []
    sources: list[dict[str, str]] = []
    loose_gml: list[Path] = []
    for dropped in sorted(source_dir.rglob("*")):
        if not dropped.is_file():
            continue
        suffix = dropped.suffix.lower()
        if suffix == ".zip":
            sources.append({"name": dropped.name, "sha256": file_sha256(dropped)})
            safe_extract_zip(dropped, workdir / dropped.stem)
        elif suffix in {".xml", ".gml"}:
            sources.append({"name": dropped.name, "sha256": file_sha256(dropped)})
            loose_gml.append(dropped)
    # FGD packs the prefecture selection as a zip of per-mesh zips; unpack one
    # more level so the leaf GML files surface.
    for nested in sorted(workdir.rglob("*.zip")):
        safe_extract_zip(nested, nested.with_suffix(""))
    extracted = [path for path in sorted(workdir.rglob("*")) if path.suffix.lower() in {".xml", ".gml"}]
    candidates = loose_gml + extracted
    buildings = [path for path in candidates if _is_building_gml(path.name)]
    return (buildings or candidates), sources


def _read_source_manifest(output: Path) -> dict[str, Any]:
    path = output / "source_manifest.json"
    if not path.is_file():
        return {}
    return read_json_object(path, label="FGD source manifest")


def build(*, output: Path = OUTPUT, source_dir: Path | None = None) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    retrieved_at = utc_timestamp()
    pin = _read_source_manifest(output)
    vintage = pin.get("publication_vintage")
    source_updated_at = vintage or "unknown (record publication_vintage in source_manifest.json)"
    dataset_id = f"{DATASET_BASE}-{vintage}" if vintage else DATASET_BASE
    prefectures = list(pin.get("prefectures", PREFECTURES))
    if source_dir is None:
        source_dir = output / "source"
    with tempfile.TemporaryDirectory(prefix="terrai-fgd-kanto-") as temporary:
        gml_files, sources = collect_building_gml(source_dir, Path(temporary))
        if not gml_files:
            raise RuntimeError(
                f"no 基盤地図情報 building GML found under {source_dir}; download the FGD "
                "「建築物の外周線」 archive(s) (see this module's docstring) and place them there"
            )
        collection = StreamedCollection(
            output / "buildings.geojson",
            dataset_id,
            {
                "source_updated_at": source_updated_at,
                "retrieved_at": retrieved_at,
                "license": LICENSE,
                "scope": SCOPE,
            },
        )
        skipped: list[str] = []
        try:
            for feature in iter_building_features(
                gml_files, retrieved_at, source_updated_at, dataset_id, skipped=skipped
            ):
                collection.add(feature)
        except BaseException:
            collection.discard()
            raise
        collection.close()
    product = output / "buildings.geojson"
    try:
        product_path = str(product.relative_to(ROOT))
    except ValueError:  # test/offline runs write outside the repository
        product_path = str(product)
    manifest = {
        "retrieved_at": retrieved_at,
        "scope": SCOPE,
        "dataset_id": dataset_id,
        "output": product_path,
        "source_updated_at": source_updated_at,
        "prefectures": prefectures,
        "license": LICENSE,
        "feature_count": collection.count,
        "invalid_geometries_skipped": len(skipped),
        "service_url": SERVICE_URL,
        "sources": sources,
    }
    write_json_atomic(output / "metadata.json", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="accepted for data-task compatibility")
    parser.parse_args()
    manifest = build()
    print(f"Wrote 基盤地図情報 Kanto buildings: {manifest['feature_count']} features")


if __name__ == "__main__":
    main()
