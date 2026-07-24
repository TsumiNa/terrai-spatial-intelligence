import json
import zipfile
from pathlib import Path

import pytest

from scripts.fetch_fgd_kanto_buildings import (
    LICENSE,
    SERVICE_URL,
    WINDOW,
    _intersects_window,
    build,
    iter_building_features,
    parse_fgd_buildings,
)

# A synthetic 基盤地図情報 GML pinning the parser to the documented FGD schema:
# the FGD_GMLSchema namespace, GML 3.2 geometry, posList as "lat lon …", a hole,
# a ring split across two curve segments sharing a joint, an out-of-window
# feature, a BldL line (must be ignored), and a degenerate BldA (no valid ring).
FIXTURE_GML = """<?xml version="1.0" encoding="UTF-8"?>
<Dataset xmlns="http://fgd.gsi.go.jp/spec/2008/FGD_GMLSchema"
         xmlns:gml="http://www.opengis.net/gml/3.2" gml:id="Dataset1">
  <BldA gml:id="K1_1">
    <fid>fgoid:10-BLD-1</fid>
    <lfSpanFr><gml:timePosition>2023-01-01</gml:timePosition></lfSpanFr>
    <type>普通建物</type>
    <area>
      <gml:Surface gml:id="K1_1-g" srsName="fguuid:jgd2011.bl">
        <gml:patches><gml:PolygonPatch><gml:exterior><gml:Ring><gml:curveMember>
          <gml:Curve gml:id="K1_1-c"><gml:segments><gml:LineStringSegment>
            <gml:posList>35.4400 139.6000 35.4400 139.6010 35.4410 139.6010 35.4410 139.6000 35.4400 139.6000</gml:posList>
          </gml:LineStringSegment></gml:segments></gml:Curve>
        </gml:curveMember></gml:Ring></gml:exterior></gml:PolygonPatch></gml:patches>
      </gml:Surface>
    </area>
  </BldA>
  <BldA gml:id="K1_2">
    <type>堅ろう建物</type>
    <area>
      <gml:Surface gml:id="K1_2-g">
        <gml:patches><gml:PolygonPatch>
          <gml:exterior><gml:Ring><gml:curveMember><gml:Curve gml:id="K1_2-e"><gml:segments><gml:LineStringSegment>
            <gml:posList>35.4500 139.6100 35.4500 139.6120 35.4520 139.6120 35.4520 139.6100 35.4500 139.6100</gml:posList>
          </gml:LineStringSegment></gml:segments></gml:Curve></gml:curveMember></gml:Ring></gml:exterior>
          <gml:interior><gml:Ring><gml:curveMember><gml:Curve gml:id="K1_2-i"><gml:segments><gml:LineStringSegment>
            <gml:posList>35.4505 139.6105 35.4505 139.6110 35.4510 139.6110 35.4510 139.6105 35.4505 139.6105</gml:posList>
          </gml:LineStringSegment></gml:segments></gml:Curve></gml:curveMember></gml:Ring></gml:interior>
        </gml:PolygonPatch></gml:patches>
      </gml:Surface>
    </area>
  </BldA>
  <BldA gml:id="K1_6">
    <type>普通建物</type>
    <area>
      <gml:Surface gml:id="K1_6-g">
        <gml:patches><gml:PolygonPatch><gml:exterior><gml:Ring>
          <gml:curveMember><gml:Curve gml:id="K1_6-a"><gml:segments><gml:LineStringSegment>
            <gml:posList>35.4600 139.6200 35.4600 139.6210 35.4610 139.6210</gml:posList>
          </gml:LineStringSegment></gml:segments></gml:Curve></gml:curveMember>
          <gml:curveMember><gml:Curve gml:id="K1_6-b"><gml:segments><gml:LineStringSegment>
            <gml:posList>35.4610 139.6210 35.4610 139.6200 35.4600 139.6200</gml:posList>
          </gml:LineStringSegment></gml:segments></gml:Curve></gml:curveMember>
        </gml:Ring></gml:exterior></gml:PolygonPatch></gml:patches>
      </gml:Surface>
    </area>
  </BldA>
  <BldA gml:id="K1_3">
    <fid>fgoid:10-BLD-3</fid>
    <type>普通建物</type>
    <area>
      <gml:Surface gml:id="K1_3-g">
        <gml:patches><gml:PolygonPatch><gml:exterior><gml:Ring><gml:curveMember>
          <gml:Curve gml:id="K1_3-c"><gml:segments><gml:LineStringSegment>
            <gml:posList>0.0000 0.0000 0.0000 0.0010 0.0010 0.0010 0.0010 0.0000 0.0000 0.0000</gml:posList>
          </gml:LineStringSegment></gml:segments></gml:Curve>
        </gml:curveMember></gml:Ring></gml:exterior></gml:PolygonPatch></gml:patches>
      </gml:Surface>
    </area>
  </BldA>
  <BldL gml:id="K1_4">
    <type>普通建物</type>
    <loc><gml:Curve gml:id="K1_4-c"><gml:segments><gml:LineStringSegment>
      <gml:posList>35.4400 139.6000 35.4410 139.6010</gml:posList>
    </gml:LineStringSegment></gml:segments></gml:Curve></loc>
  </BldL>
  <BldA gml:id="K1_5">
    <type>普通建物</type>
    <area>
      <gml:Surface gml:id="K1_5-g">
        <gml:patches><gml:PolygonPatch><gml:exterior><gml:Ring><gml:curveMember>
          <gml:Curve gml:id="K1_5-c"><gml:segments><gml:LineStringSegment>
            <gml:posList>35.4400 139.6000 35.4400 139.6010</gml:posList>
          </gml:LineStringSegment></gml:segments></gml:Curve>
        </gml:curveMember></gml:Ring></gml:exterior></gml:PolygonPatch></gml:patches>
      </gml:Surface>
    </area>
  </BldA>
</Dataset>
"""

# The per-mesh filename FGD uses; the mesh token disambiguates fid-less features.
GML_NAME = "FG-GML-5339-00-BldA-20230101-0001.xml"


def write_fixture(directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / GML_NAME
    path.write_text(FIXTURE_GML, encoding="utf-8")
    return path


def test_window_intersection_uses_the_kanto_bounds() -> None:
    west, south, east, north = WINDOW
    assert _intersects_window((west + 0.1, south + 0.1, west + 0.2, south + 0.2))
    assert _intersects_window((west - 0.1, south + 0.1, west + 0.1, south + 0.2))  # straddling
    assert not _intersects_window((0.0, 0.0, 1.0, 1.0))


def test_parse_reads_blda_swaps_coordinates_and_ignores_bldl(tmp_path: Path) -> None:
    path = write_fixture(tmp_path)
    parsed = list(parse_fgd_buildings(path))

    # Six BldA (K1_1,2,3,5,6 + none from BldL); K1_5 degenerate -> no geometry.
    kinds = [gml_id for gml_id, *_ in parsed]
    assert kinds == ["K1_1", "K1_2", "K1_6", "K1_3", "K1_5"]  # BldL K1_4 excluded

    by_id = {gml_id: (type_text, fid, geom) for gml_id, type_text, fid, geom in parsed}
    k1_1_type, k1_1_fid, k1_1_geom = by_id["K1_1"]
    # lat lon -> [lon, lat]; ring closed.
    assert k1_1_geom["coordinates"][0][0] == [139.6, 35.44]
    assert k1_1_geom["coordinates"][0][-1] == [139.6, 35.44]
    assert k1_1_type == "普通建物"
    assert k1_1_fid == "fgoid:10-BLD-1"
    # K1_2 has a hole -> two rings.
    assert len(by_id["K1_2"][2]["coordinates"]) == 2
    # K1_5 degenerate two-point ring -> no geometry.
    assert by_id["K1_5"][2] is None


def test_split_ring_segments_dedupe_the_shared_joint(tmp_path: Path) -> None:
    path = write_fixture(tmp_path)
    parsed = {gml_id: geom for gml_id, _type, _fid, geom in parse_fgd_buildings(path)}
    ring = parsed["K1_6"]["coordinates"][0]
    # Four distinct corners + the repeated closing vertex, no duplicated joint.
    assert ring == [[139.62, 35.46], [139.621, 35.46], [139.621, 35.461], [139.62, 35.461], [139.62, 35.46]]


def test_only_in_window_buildings_survive_with_identity_and_provenance(tmp_path: Path) -> None:
    path = write_fixture(tmp_path)
    skipped: list[str] = []
    features = list(
        iter_building_features([path], "2026-07-24T00:00:00Z", "2023-01-01", "fgd-kanto-buildings-2023-01-01", skipped=skipped)
    )

    # K1_1, K1_2, K1_6 in-window; K1_3 outside; K1_5 degenerate -> skipped.
    ids = [feature["properties"]["fgd_id"] for feature in features]
    assert ids == ["fgoid:10-BLD-1", "5339-00:K1_2", "5339-00:K1_6"]
    assert len(skipped) == 1

    first = features[0]["properties"]
    assert first["footprint_source"] == "fgd"
    assert first["fgd_id"] == "fgoid:10-BLD-1"  # the fid is preferred over the gml:id
    assert first["fgd_type"] == "普通建物"
    assert first["terrai_source_url"] == SERVICE_URL
    assert first["terrai_source_updated_at"] == "2023-01-01"
    assert first["terrai_retrieved_at"] == "2026-07-24T00:00:00Z"
    # Fid-less feature falls back to a mesh-namespaced gml:id.
    assert features[1]["properties"]["fgd_gml_id"] == "K1_2"


def test_build_writes_a_valid_collection_and_manifest_from_a_directory(tmp_path: Path) -> None:
    source = tmp_path / "source"
    write_fixture(source)

    manifest = build(output=tmp_path / "out", source_dir=source)

    collection = json.loads((tmp_path / "out/buildings.geojson").read_text(encoding="utf-8"))
    assert collection["type"] == "FeatureCollection"
    assert "測量法" in collection["metadata"]["license"]
    assert len(collection["features"]) == 3
    assert all(feature["properties"]["footprint_source"] == "fgd" for feature in collection["features"])
    assert manifest["feature_count"] == 3
    assert manifest["invalid_geometries_skipped"] == 1
    assert manifest["license"] == LICENSE
    assert manifest["prefectures"] == ["Tokyo", "Kanagawa", "Chiba", "Saitama"]
    assert manifest["service_url"] == SERVICE_URL
    assert manifest["sources"][0]["name"] == GML_NAME
    assert manifest["sources"][0]["sha256"]
    written = json.loads((tmp_path / "out/metadata.json").read_text(encoding="utf-8"))
    assert written == manifest


def test_build_extracts_a_zip_archive(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir(parents=True)
    with zipfile.ZipFile(source / "pack.zip", "w") as archive:
        archive.writestr(GML_NAME, FIXTURE_GML)

    manifest = build(output=tmp_path / "out", source_dir=source)

    assert manifest["feature_count"] == 3
    assert manifest["sources"][0]["name"] == "pack.zip"


def test_build_reads_vintage_from_the_source_manifest(tmp_path: Path) -> None:
    output = tmp_path / "out"
    output.mkdir(parents=True)
    (output / "source_manifest.json").write_text(
        json.dumps({"publication_vintage": "2023-01-01", "prefectures": ["Tokyo"]}), encoding="utf-8"
    )
    write_fixture(output / "source")

    manifest = build(output=output)

    assert manifest["dataset_id"] == "fgd-kanto-buildings-2023-01-01"
    assert manifest["source_updated_at"] == "2023-01-01"
    assert manifest["prefectures"] == ["Tokyo"]


def test_build_without_the_archive_raises_a_pointed_error(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="建築物の外周線"):
        build(output=tmp_path / "out", source_dir=tmp_path / "missing")
