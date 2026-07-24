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

**Coverage is mainland Kanto only.** The FGD service sells buildings by whole
prefecture, and 東京都 legally reaches the far Pacific — the Izu Islands, the
Ogasawara/Bonin chain, and even Minamitorishima (154°E) and Okinotorishima
(20°N), 1000+ km out. Those are irrelevant to a mainland-Kanto exhibition and
would blow the coverage window out to 1600 km, so this task **drops every mesh
outside ``MAINLAND_BOUNDS``** and records how many island meshes it excluded.
The retained meshes define the coverage footprint (``coverage.json``) that the
merge clips OSM to and the frontend uses for the out-of-service boundary.

Manual, registration-gated acquisition — reproduce the pinned input like this:

1. Register (free) at the Fundamental Geospatial Data download service at
   https://service.gsi.go.jp/kiban/ — account creation and the authenticated
   download are a human step; this task never fetches over the network.
2. Select the product 「建築物の外周線」 (building outlines, feature type ``BldA``)
   for the four mainland-Kanto prefectures — Tokyo, Kanagawa, Chiba, Saitama.
3. Download the JPGIS(GML) archive(s) and drop them into
   ``data/fgd/kanto_buildings/source/``. The download packs per-mesh zips
   (``FG-GML-<mesh6>-11-<date>.zip``); a folder of them, or the whole bundle
   zip, or loose GML are all accepted, and duplicate meshes across bundles are
   de-duplicated by their 6-digit 2次メッシュ code.
4. Record the publication vintage in
   ``data/fgd/kanto_buildings/source_manifest.json`` (``publication_vintage``).
5. Run ``uv run python scripts/fetch_fgd_kanto_buildings.py``. It writes the
   gitignored ``buildings.geojson`` product, the committed ``metadata.json`` and
   ``coverage.json``; commit the two manifests.

The FGD JPGIS GML flavour (custom ``FGD_GMLSchema`` namespace, GML 3.2 geometry,
JGD2024 geographic which equals WGS84 to sub-metre in Japan) is parsed directly
with the stdlib XML reader and local-name matching rather than through OGR, whose
FGD handling is inconsistent across builds; a synthetic fixture in the test pins
the parser to the documented schema.
"""

from __future__ import annotations

import argparse
import hashlib
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
from terrai_spatial.store import feature_bbox  # noqa: E402

SERVICE_URL = "https://service.gsi.go.jp/kiban/"
DATASET_BASE = "fgd-kanto-buildings"
OUTPUT = ROOT / "data/fgd/kanto_buildings"
# 承認申請-exempt basic-survey content; attribution + a processing note suffice.
LICENSE = "基盤地図情報 (GSI) — 測量法 承認申請-exempt; attribution + 加工表示 (processing note) required"
SCOPE = "TerrAI Kanto acquisition: 基盤地図情報 building outlines filling OSM's gaps inside the mainland window"
PREFECTURES = ("Tokyo", "Kanagawa", "Chiba", "Saitama")

# Generous mainland-Kanto gate (W, S, E, N). Meshes/features outside it — Tokyo's
# Izu/Ogasawara islands, Minamitorishima, Okinotorishima — are dropped. The tight
# coverage bbox is derived from the meshes that survive this gate.
MAINLAND_BOUNDS = (138.4, 34.8, 141.2, 36.5)

# 2次メッシュ (secondary grid) cell size in degrees: 5′ lat × 7.5′ lon.
MESH_LAT_DEG = 1 / 12
MESH_LON_DEG = 1 / 8

# The FGD download packages 「建築物の外周線」 as ``BldA`` area features; the
# per-mesh files carry that token (romanized) in their name, and the 6-digit
# 2次メッシュ code appears right after ``FG-GML-``.
BUILDING_FEATURE = "BldA"
_MESH_RE = re.compile(r"FG-GML-(\d{6})")


def _local(tag: str) -> str:
    """The local name of a namespaced XML tag (``{ns}Bld`` -> ``Bld``)."""

    return tag.rsplit("}", 1)[-1]


def _gml_id(element: ElementTree.Element) -> str | None:
    for key, value in element.attrib.items():
        if _local(key) == "id":
            return value
    return None


def mesh_cell(code: str) -> tuple[float, float, float, float]:
    """The (W, S, E, N) degree bounds of a 6-digit 2次メッシュ code."""

    lat_first = int(code[0:2]) / 1.5
    lon_first = int(code[2:4]) + 100
    south = lat_first + int(code[4]) * MESH_LAT_DEG
    west = lon_first + int(code[5]) * MESH_LON_DEG
    return west, south, west + MESH_LON_DEG, south + MESH_LAT_DEG


def is_mainland_mesh(code: str) -> bool:
    """Whether a mesh cell lies wholly within the mainland-Kanto gate."""

    west, south, east, north = mesh_cell(code)
    gw, gs, ge, gn = MAINLAND_BOUNDS
    return south >= gs and north <= gn and west >= gw and east <= ge


def _mesh_of(name: str) -> str | None:
    match = _MESH_RE.search(name)
    return match.group(1) if match else None


def _ring_from(element: ElementTree.Element) -> list[list[float]]:
    """Concatenate every ``gml:posList`` under ``element`` into one closed ring.

    FGD posLists are ``lat lon lat lon …`` (JGD2024 geographic, which equals
    WGS84 to sub-metre in Japan), so each pair is swapped to GeoJSON ``[lon,
    lat]``. A ring may be split across consecutive curve segments whose shared
    joint is repeated; that duplicate is dropped, and the ring is closed.
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
    # grow with the mesh file's feature count (a dense mesh's BldA is ~100 MB).
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


def _intersects_mainland(bbox: tuple[float, float, float, float]) -> bool:
    west, south, east, north = MAINLAND_BOUNDS
    return bbox[2] >= west and bbox[0] <= east and bbox[3] >= south and bbox[1] <= north


def iter_building_features(
    gml_files: list[Path],
    retrieved_at: str,
    source_updated_at: str,
    dataset_id: str,
    *,
    skipped: list[str] | None = None,
) -> Iterator[dict[str, Any]]:
    """Every FGD building outline inside the mainland window, with provenance.

    The FGD identifier is the globally-unique feature id (``fid``) when the file
    carries one; otherwise the per-file ``gml:id`` is namespaced with its mesh
    code so it stays unique across the hundreds of mesh files in one download.
    """

    for gml_path in gml_files:
        # Always a stable label: the 6-digit mesh where the name carries one,
        # else the file stem — never "None:<id>".
        mesh = _mesh_of(gml_path.name) or gml_path.stem
        for gml_id, type_text, fid_text, geometry in parse_fgd_buildings(gml_path):
            if geometry is None:
                if skipped is not None:
                    skipped.append(fid_text or (f"{mesh}:{gml_id}" if gml_id else mesh))
                continue
            bbox = feature_bbox(geometry)
            if bbox is None or not _intersects_mainland(bbox):
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
    """A BldA (area) building file — not the BldL line file or the index."""

    return BUILDING_FEATURE in name or "建築物の外周線" in name


class Collected:
    """The result of walking the pinned source tree."""

    def __init__(self) -> None:
        self.gml_files: list[Path] = []
        self.sources: list[dict[str, Any]] = []
        self.covered: set[str] = set()
        self.excluded_islands: set[str] = set()


def _admit(mesh: str | None, result: Collected, contributed: list[str]) -> bool:
    """Whether a mesh's files should be read: mainland, and not already seen."""

    if mesh is None:
        return True  # loose GML with no mesh code (e.g. the test fixture)
    if not is_mainland_mesh(mesh):
        result.excluded_islands.add(mesh)
        return False
    if mesh in result.covered:
        return False  # the same mesh in an earlier bundle
    result.covered.add(mesh)
    contributed.append(mesh)
    return True


def collect_building_gml(source_dir: Path, workdir: Path) -> Collected:
    """Walk the pinned source tree, keeping mainland BldA GML, deduped by mesh.

    Each top-level item under ``source_dir`` (a download-bundle folder, a bundle
    zip that nests per-mesh zips, or loose GML) becomes one ``sources`` record
    with a content digest and the number of meshes it contributed. Island meshes
    are skipped, and a mesh already seen in an earlier bundle is not read twice.
    """

    result = Collected()
    if not source_dir.is_dir():
        return result

    for index, bundle in enumerate(sorted(source_dir.iterdir())):
        # Stage the bundle into a directory we can glob: a folder is used as-is,
        # a bundle zip is extracted first (its members are per-mesh zips), and a
        # single loose GML is handled directly.
        if bundle.is_dir():
            staging: Path | None = bundle
        elif bundle.suffix.lower() == ".zip":
            staging = workdir / f"bundle{index}"
            safe_extract_zip(bundle, staging)
        elif bundle.suffix.lower() in {".xml", ".gml"}:
            staging = None
        else:
            continue

        mesh_zips = sorted(staging.rglob("*.zip")) if staging else []
        loose_gml = (
            [p for p in sorted(staging.rglob("*")) if p.suffix.lower() in {".xml", ".gml"}]
            if staging
            else [bundle]
        )

        digest_parts: list[str] = []
        contributed: list[str] = []

        for zip_path in mesh_zips:
            mesh = _mesh_of(zip_path.name)
            if not _admit(mesh, result, contributed):
                continue
            digest_parts.append(f"{zip_path.name}:{file_sha256(zip_path)}")
            destination = workdir / f"mesh{index}" / (mesh or zip_path.stem)
            safe_extract_zip(zip_path, destination)
            for extracted in sorted(destination.rglob("*")):
                if extracted.suffix.lower() in {".xml", ".gml"} and _is_building_gml(extracted.name):
                    result.gml_files.append(extracted)

        for gml_path in loose_gml:
            mesh = _mesh_of(gml_path.name)
            if not _admit(mesh, result, contributed):
                continue
            if _is_building_gml(gml_path.name) or mesh is None:
                result.gml_files.append(gml_path)
                digest_parts.append(f"{gml_path.name}:{file_sha256(gml_path)}")

        if digest_parts:
            bundle_sha = hashlib.sha256("\n".join(sorted(digest_parts)).encode("utf-8")).hexdigest()
            result.sources.append(
                {"name": bundle.name, "mesh_count": len(contributed), "sha256": bundle_sha}
            )

    return result


def coverage_footprint(dataset_id: str, covered: list[str], excluded: list[str]) -> dict[str, Any]:
    """The mainland mesh set + its bbox, for the merge clip and the map boundary."""

    cells = [mesh_cell(code) for code in covered]
    bbox = None
    if cells:
        bbox = [
            round(min(c[0] for c in cells), 6),
            round(min(c[1] for c in cells), 6),
            round(max(c[2] for c in cells), 6),
            round(max(c[3] for c in cells), 6),
        ]
    return {
        "dataset_id": dataset_id,
        "grid": "JIS 2次メッシュ (secondary mesh)",
        "mesh_size_deg": {"lat": MESH_LAT_DEG, "lon": MESH_LON_DEG},
        "mesh_count": len(covered),
        "bbox": bbox,
        "meshes": covered,
        "excluded_island_mesh_count": len(excluded),
        "excluded_island_meshes": excluded,
        "note": (
            "Mainland Kanto only. The FGD download for whole 東京都 includes the "
            "Izu/Ogasawara islands and the remote Pacific outposts (Minamitorishima "
            "154°E, Okinotorishima 20°N); those meshes are excluded (see MAINLAND_BOUNDS "
            "in scripts/fetch_fgd_kanto_buildings.py) so the coverage stays mainland."
        ),
    }


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
        collected = collect_building_gml(source_dir, Path(temporary))
        if not collected.gml_files:
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
                collected.gml_files, retrieved_at, source_updated_at, dataset_id, skipped=skipped
            ):
                collection.add(feature)
        except BaseException:
            collection.discard()
            raise
        collection.close()

    covered = sorted(collected.covered)
    excluded = sorted(collected.excluded_islands)
    coverage = coverage_footprint(dataset_id, covered, excluded)
    write_json_atomic(output / "coverage.json", coverage)

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
        "mesh_count": coverage["mesh_count"],
        "coverage_bbox": coverage["bbox"],
        "excluded_island_mesh_count": coverage["excluded_island_mesh_count"],
        "service_url": SERVICE_URL,
        "sources": collected.sources,
    }
    write_json_atomic(output / "metadata.json", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="accepted for data-task compatibility")
    parser.parse_args()
    manifest = build()
    print(
        f"Wrote 基盤地図情報 Kanto buildings: {manifest['feature_count']} features "
        f"across {manifest['mesh_count']} mainland meshes "
        f"({manifest['excluded_island_mesh_count']} island meshes excluded)"
    )


if __name__ == "__main__":
    main()
