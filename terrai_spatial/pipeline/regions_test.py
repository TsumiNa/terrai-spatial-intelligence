from __future__ import annotations

from terrai_spatial.pipeline import regions


def test_registry_pins_the_exact_values_the_scripts_use() -> None:
    assert regions.STUDY_BOUNDS == {
        "yokohama": (139.5835, 35.4426, 139.5935, 35.4504),
        "mobara": (140.2757, 35.4387, 140.2913, 35.4513),
    }
    assert regions.MLIT_ACQUISITION_BOUNDS == {
        "kanto": (138.65, 34.85, 140.95, 36.30),
        "hakone_west": (138.90, 35.10, 139.00, 35.33),
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
        *regions.MLIT_ACQUISITION_BOUNDS.values(),
        regions.SAPPORO_UNDERGROUND_ACCESS_BOUNDS,
    ]
    for west, south, east, north in all_bounds:
        assert west < east
        assert south < north


def test_the_kanto_acquisition_window_contains_every_analysis_window() -> None:
    kanto_west, kanto_south, kanto_east, kanto_north = regions.MLIT_ACQUISITION_BOUNDS["kanto"]
    for west, south, east, north in regions.STUDY_BOUNDS.values():
        assert kanto_west < west
        assert kanto_south < south
        assert kanto_east > east
        assert kanto_north > north


def test_the_hakone_clip_sits_inside_the_kanto_window() -> None:
    kanto_west, kanto_south, kanto_east, kanto_north = regions.MLIT_ACQUISITION_BOUNDS["kanto"]
    west, south, east, north = regions.MLIT_ACQUISITION_BOUNDS["hakone_west"]
    assert kanto_west <= west and kanto_south <= south
    assert kanto_east >= east and kanto_north >= north
