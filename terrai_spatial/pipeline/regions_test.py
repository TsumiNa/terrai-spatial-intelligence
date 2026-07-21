from __future__ import annotations

from terrai_spatial.pipeline import regions


def test_registry_pins_the_exact_values_the_scripts_used_before() -> None:
    assert regions.STUDY_BOUNDS == {
        "yokohama": (139.5835, 35.4426, 139.5935, 35.4504),
        "mobara": (140.2757, 35.4387, 140.2913, 35.4513),
    }
    assert regions.MLIT_CONTEXT_BOUNDS == {
        "yokohama": (139.54, 35.39, 139.66, 35.515),
        "mobara": (140.22, 35.38, 140.35, 35.51),
    }
    assert regions.SAPPORO_UNDERGROUND_ACCESS_BOUNDS == (
        141.349592632,
        43.054916388,
        141.356913521,
        43.070980841,
    )


def test_every_bounds_follows_the_west_south_east_north_convention() -> None:
    all_bounds = [
        *regions.STUDY_BOUNDS.values(),
        *regions.MLIT_CONTEXT_BOUNDS.values(),
        regions.SAPPORO_UNDERGROUND_ACCESS_BOUNDS,
    ]
    for west, south, east, north in all_bounds:
        assert west < east
        assert south < north


def test_acquisition_context_strictly_contains_its_analysis_window() -> None:
    for region, (west, south, east, north) in regions.STUDY_BOUNDS.items():
        context_west, context_south, context_east, context_north = regions.MLIT_CONTEXT_BOUNDS[region]
        assert context_west < west
        assert context_south < south
        assert context_east > east
        assert context_north > north
