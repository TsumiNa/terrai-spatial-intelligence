import io

from scripts.fetch_plateau_kanto_buildings import iter_building_heights

# A synthetic PLATEAU CityGML pinning the parser: bldg:Building with
# measuredHeight + a lod0FootPrint (lat lon z triples); a building with no height
# (skipped); and one using lod1Solid instead of a footprint.
FIXTURE = """<?xml version="1.0" encoding="UTF-8"?>
<core:CityModel xmlns:core="http://www.opengis.net/citygml/2.0"
                xmlns:bldg="http://www.opengis.net/citygml/building/2.0"
                xmlns:gml="http://www.opengis.net/gml">
  <core:cityObjectMember>
    <bldg:Building gml:id="bldg_1">
      <bldg:measuredHeight uom="m">12.5</bldg:measuredHeight>
      <bldg:lod0FootPrint><gml:MultiSurface><gml:surfaceMember><gml:Polygon><gml:exterior><gml:LinearRing>
        <gml:posList>35.900 139.280 0 35.900 139.282 0 35.902 139.282 0 35.902 139.280 0 35.900 139.280 0</gml:posList>
      </gml:LinearRing></gml:exterior></gml:Polygon></gml:surfaceMember></gml:MultiSurface></bldg:lod0FootPrint>
    </bldg:Building>
  </core:cityObjectMember>
  <core:cityObjectMember>
    <bldg:Building gml:id="bldg_2">
      <bldg:lod0FootPrint><gml:MultiSurface><gml:surfaceMember><gml:Polygon><gml:exterior><gml:LinearRing>
        <gml:posList>35.900 139.290 0 35.900 139.291 0 35.901 139.291 0 35.900 139.290 0</gml:posList>
      </gml:LinearRing></gml:exterior></gml:Polygon></gml:surfaceMember></gml:MultiSurface></bldg:lod0FootPrint>
    </bldg:Building>
  </core:cityObjectMember>
  <core:cityObjectMember>
    <bldg:Building gml:id="bldg_3">
      <bldg:measuredHeight uom="m">30</bldg:measuredHeight>
      <bldg:lod1Solid><gml:Solid><gml:exterior><gml:CompositeSurface><gml:surfaceMember><gml:Polygon>
        <gml:exterior><gml:LinearRing>
        <gml:posList>35.800 139.700 0 35.800 139.702 0 35.802 139.702 0 35.802 139.700 0 35.800 139.700 0</gml:posList>
      </gml:LinearRing></gml:exterior></gml:Polygon></gml:surfaceMember></gml:CompositeSurface></gml:exterior></gml:Solid></bldg:lod1Solid>
    </bldg:Building>
  </core:cityObjectMember>
</core:CityModel>
"""


def test_extracts_measured_height_and_footprint_centroid_swapping_coords():
    features = list(iter_building_heights(io.BytesIO(FIXTURE.encode("utf-8")), "11326"))

    # bldg_2 has no measuredHeight -> skipped; bldg_1 (footprint) + bldg_3 (solid) kept.
    ids = [f["properties"]["plateau_id"] for f in features]
    assert ids == ["bldg_1", "bldg_3"]

    one = features[0]
    assert one["geometry"]["type"] == "Point"
    lon, lat = one["geometry"]["coordinates"]
    # lat lon z -> [lon, lat]; centroid of the (closed) footprint ring.
    assert round(lon, 3) == 139.281
    assert round(lat, 3) == 35.901
    assert one["properties"]["height"] == 12.5
    assert one["properties"]["municipality"] == "11326"

    # lod1Solid is used when there is no lod0FootPrint.
    assert features[1]["properties"]["height"] == 30.0
    assert round(features[1]["geometry"]["coordinates"][0], 3) == 139.701


def test_zero_or_missing_height_is_skipped():
    no_height = FIXTURE.replace('<bldg:measuredHeight uom="m">12.5</bldg:measuredHeight>', "")
    features = list(iter_building_heights(io.BytesIO(no_height.encode("utf-8")), "11326"))
    assert [f["properties"]["plateau_id"] for f in features] == ["bldg_3"]
