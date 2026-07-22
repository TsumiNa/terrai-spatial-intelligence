"""The study-area registry: every region bounding box, defined once.

Convention: ``(west, south, east, north)`` in EPSG:4326 degrees, everywhere.
Scripts that need another shape (tile schemes, per-corner transforms) convert
at the point of use rather than re-declaring the numbers.

Decisions this module records, so they are not rediscovered per script:

- The analysis windows in ``STUDY_BOUNDS`` and the wider boxes in
  ``MLIT_CONTEXT_BOUNDS`` are deliberately different. MLIT layers are acquired
  with surrounding context so features straddling the analysis window arrive
  whole; the analyses themselves stay inside the study windows.
- The two build scripts' planar-approximation reference latitudes (35.4465
  and 35.446) disagreed by accident, not intent. They are formulas, not
  bounding boxes, so they stay in the scripts until the
  ``projected-crs-measurement`` refactor deletes the planar approximation
  entirely — a projected CRS has no reference latitude to disagree about.
- The Nihonbashi underground extent is computed from the ingested 3D Tiles
  bounding regions rather than declared, and stays that way.
"""

from __future__ import annotations


Bounds = tuple[float, float, float, float]

# The demonstration analysis windows. These are the numbers every analysis,
# tile cache and embedding crop used before this registry existed.
STUDY_BOUNDS: dict[str, Bounds] = {
    "yokohama": (139.5835, 35.4426, 139.5935, 35.4504),
    "mobara": (140.2757, 35.4387, 140.2913, 35.4513),
}

# Wider acquisition context for the MLIT foundation subsets — intentional,
# not drift; see the module docstring.
MLIT_CONTEXT_BOUNDS: dict[str, Bounds] = {
    "yokohama": (139.54, 35.39, 139.66, 35.515),
    "mobara": (140.22, 35.38, 140.35, 35.51),
}

# The wide acquisition windows for the Kanto foundation coverage
# (docs/refactor/kanto-foundation-coverage/00-overview.md). "kanto" covers
# mainland Tokyo, Kanagawa, Chiba and Saitama with margin, excluding the
# Izu/Ogasawara islands; "hakone_west" clips land-use-mesh sheet 5238 to
# Kanagawa's western sliver instead of ingesting a block of Shizuoka.
MLIT_WIDE_BOUNDS: dict[str, Bounds] = {
    "kanto": (138.65, 34.85, 140.95, 36.30),
    "hakone_west": (138.90, 35.10, 139.00, 35.33),
}

# The bounded Overpass window for the Sapporo underground access snapshot.
SAPPORO_UNDERGROUND_ACCESS_BOUNDS: Bounds = (141.349592632, 43.054916388, 141.356913521, 43.070980841)
