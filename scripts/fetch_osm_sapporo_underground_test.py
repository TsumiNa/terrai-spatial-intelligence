from __future__ import annotations

import pytest

from scripts.fetch_osm_sapporo_underground import normalize_snapshot


def node(element_id: int, tags: dict, *, version: int = 2) -> dict:
    return {
        "type": "node",
        "id": element_id,
        "lat": 43.06,
        "lon": 141.35,
        "version": version,
        "changeset": 123,
        "timestamp": "2026-07-01T00:00:00Z",
        "tags": tags,
    }


def way(element_id: int, tags: dict) -> dict:
    return {
        "type": "way",
        "id": element_id,
        "version": 4,
        "changeset": 456,
        "timestamp": "2026-07-02T00:00:00Z",
        "tags": tags,
        "geometry": [
            {"lat": 43.06, "lon": 141.35},
            {"lat": 43.061, "lon": 141.351},
        ],
    }


def snapshot(elements: list[dict]) -> dict:
    return {
        "generator": "Overpass API test",
        "osm3s": {"timestamp_osm_base": "2026-07-21T00:00:00Z"},
        "elements": elements,
    }


def normalize(elements: list[dict]) -> tuple[dict, dict]:
    return normalize_snapshot(
        snapshot(elements),
        query="[out:json];out;",
        retrieved_at="2026-07-21T01:00:00Z",
        endpoint="https://example.test/api/interpreter",
    )


def test_normalize_keeps_source_identity_tags_and_unknown_access() -> None:
    collection, metadata = normalize(
        [
            node(1, {"railway": "subway_entrance", "ref": "1"}),
            way(2, {"railway": "subway", "tunnel": "yes", "layer": "-1"}),
        ]
    )

    assert metadata["feature_count"] == 2
    entrance = next(item for item in collection["features"] if item["id"] == "osm/node/1")
    assert entrance["properties"]["osm_version"] == 2
    assert entrance["properties"]["osm_changeset"] == 123
    assert entrance["properties"]["osm_timestamp"] == "2026-07-01T00:00:00Z"
    assert entrance["properties"]["tags"] == {"railway": "subway_entrance", "ref": "1"}
    assert entrance["properties"]["public_access_status"] == "not_stated"
    assert entrance["properties"]["depth_m"] is None


def test_empty_snapshot_is_valid_and_ambiguous_level_is_not_converted() -> None:
    empty, empty_metadata = normalize([])
    assert empty["features"] == []
    assert empty_metadata["feature_count"] == 0

    collection, _ = normalize([way(3, {"highway": "corridor", "indoor": "yes", "level": "B1;0"})])
    properties = collection["features"][0]["properties"]
    assert properties["level"] == "B1;0"
    assert properties["depth_m"] is None
    assert properties["underground_evidence"] == ["indoor", "level_tag"]


def test_numeric_surface_level_is_not_mislabelled_as_underground() -> None:
    collection, metadata = normalize([way(6, {"highway": "footway", "level": "0"})])

    assert collection["features"] == []
    assert metadata["omitted_non_underground_walkways"] == 1


def test_explicitly_private_walkway_is_excluded_but_not_relabelled() -> None:
    collection, metadata = normalize(
        [way(4, {"highway": "footway", "tunnel": "yes", "access": "private"})]
    )

    assert collection["features"] == []
    assert metadata["omitted_explicitly_restricted_walkways"] == 1


def test_missing_way_geometry_is_rejected() -> None:
    broken = way(5, {"railway": "subway"})
    broken.pop("geometry")

    with pytest.raises(RuntimeError, match="lacks complete geometry"):
        normalize([broken])
