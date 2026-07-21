from __future__ import annotations

import pytest
from pyproj import Transformer

from terrai_spatial.pipeline import measurement


ROUND_TRIP_TOLERANCE_DEGREES = 1e-9

# One representative point per demonstration region, so a zone that fits
# Yokohama but not Mobara fails here rather than in a regenerated dataset.
REGION_POINTS = {
    "yokohama": (139.5885, 35.4465),
    "mobara": (140.2835, 35.4450),
}

# Expected metric separations, checked once against the GRS80 geodesic when
# these constants were written; Zone IX distortion over the demo extents is
# below 0.01%.
KNOWN_SEPARATIONS = (
    ((139.5885, 35.4426), (139.5885, 35.4526), 1109.38),
    ((139.5835, 35.4465), (139.5935, 35.4465), 907.81),
    ((139.5835, 35.4426), (139.5935, 35.4504), 1254.15),
    ((140.2757, 35.4387), (140.2913, 35.4513), 1989.89),
)


def test_both_demo_regions_round_trip_through_the_measurement_crs() -> None:
    inverse = Transformer.from_crs(measurement.MEASUREMENT_CRS, "EPSG:4326", always_xy=True)
    for longitude, latitude in REGION_POINTS.values():
        x, y = measurement.project_point((longitude, latitude))
        recovered_lon, recovered_lat = inverse.transform(x, y)
        assert recovered_lon == pytest.approx(longitude, abs=ROUND_TRIP_TOLERANCE_DEGREES)
        assert recovered_lat == pytest.approx(latitude, abs=ROUND_TRIP_TOLERANCE_DEGREES)


def test_known_separations_measure_to_their_expected_metric_values() -> None:
    for a, b, expected in KNOWN_SEPARATIONS:
        measured = measurement.distance_m(measurement.project_point(a), measurement.project_point(b))
        assert measured == pytest.approx(expected, abs=0.05)


def test_project_line_matches_per_point_projection() -> None:
    coordinates = [(139.5835, 35.4426), (139.5885, 35.4465), (139.5935, 35.4504)]
    line = measurement.project_line(coordinates)
    assert line == [measurement.project_point(point) for point in coordinates]


def test_point_segment_distance_clamps_to_the_segment_and_handles_degeneracy() -> None:
    assert measurement.point_segment_distance_m((0.0, 3.0), (0.0, 0.0), (4.0, 0.0)) == 3.0
    assert measurement.point_segment_distance_m((-3.0, 4.0), (0.0, 0.0), (4.0, 0.0)) == 5.0
    assert measurement.point_segment_distance_m((3.0, 4.0), (0.0, 0.0), (0.0, 0.0)) == 5.0


def test_point_line_distance_takes_the_nearest_segment() -> None:
    line = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0)]
    assert measurement.point_line_distance_m((11.0, 5.0), line) == 1.0
