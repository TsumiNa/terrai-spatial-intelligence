"""Projected measurement for the analysis pipelines.

Every metric quantity is measured in EPSG:6677 (JGD2011 / Japan Plane
Rectangular CS IX). Zone IX covers Kanagawa and Chiba, so both demonstration
regions measure in one zone with no cross-zone comparison problem. Storage
and delivery stay EPSG:4326 — projection happens inside the computation only,
never in the stored GeoJSON.

Project geometry once per feature collection, then measure on the projected
coordinates. The transformer is module-level and cached; constructing one per
distance call inside a nearest-neighbour loop would be pathological.
"""

from __future__ import annotations

import math
from typing import Sequence

from pyproj import Transformer


MEASUREMENT_CRS = "EPSG:6677"

_TO_PLANE = Transformer.from_crs("EPSG:4326", MEASUREMENT_CRS, always_xy=True)

XY = tuple[float, float]


def project_point(point: Sequence[float]) -> XY:
    """Project one ``[longitude, latitude]`` position into plane metres."""

    return _TO_PLANE.transform(point[0], point[1])


def project_line(coordinates: Sequence[Sequence[float]]) -> list[XY]:
    """Project a coordinate sequence in one transformer call."""

    xs, ys = _TO_PLANE.transform(
        [point[0] for point in coordinates],
        [point[1] for point in coordinates],
    )
    return list(zip(xs, ys))


def distance_m(a: XY, b: XY) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def point_segment_distance_m(point: XY, start: XY, end: XY) -> float:
    px, py = point
    ax, ay = start
    bx, by = end
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def point_line_distance_m(point: XY, line: Sequence[XY]) -> float:
    return min(
        point_segment_distance_m(point, line[index], line[index + 1])
        for index in range(len(line) - 1)
    )
