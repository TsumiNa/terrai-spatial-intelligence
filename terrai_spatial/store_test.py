from __future__ import annotations

import json
import sqlite3
import subprocess
from pathlib import Path

import pytest

from terrai_spatial import store
from terrai_spatial.data_service import ALL_DATASETS, store_sources


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def scan_intersects(geometry: dict | None, bbox: tuple[float, float, float, float]) -> bool:
    """Independent oracle replicating the retired per-query bbox scan."""

    if not geometry:
        return False
    pairs = list(store._coordinate_pairs(geometry.get("coordinates")))
    if not pairs:
        return False
    min_x, min_y, max_x, max_y = bbox
    return not (
        max(x for x, _ in pairs) < min_x
        or min(x for x, _ in pairs) > max_x
        or max(y for _, y in pairs) < min_y
        or min(y for _, y in pairs) > max_y
    )

# Edge-case fixture: a feature straddling the window edge, a multi-part
# geometry, a diagonal line whose bbox intersects while its geometry does not,
# and a feature with no usable coordinates.
EDGE_FEATURES = [
    {"type": "Feature", "id": "straddle", "geometry": {"type": "Point", "coordinates": [1.0, 0.5]}, "properties": {}},
    {
        "type": "Feature",
        "id": "multi",
        "geometry": {
            "type": "MultiPolygon",
            "coordinates": [
                [[[3.0, 3.0], [3.5, 3.0], [3.5, 3.5], [3.0, 3.0]]],
                [[[8.0, 8.0], [8.5, 8.0], [8.5, 8.5], [8.0, 8.0]]],
            ],
        },
        "properties": {},
    },
    {
        "type": "Feature",
        "id": "diagonal",
        "geometry": {"type": "LineString", "coordinates": [[2.0, 6.0], [6.0, 2.0]]},
        "properties": {},
    },
    {"type": "Feature", "id": "empty", "geometry": {"type": "GeometryCollection", "geometries": []}, "properties": {}},
]


def write_fixture_root(root: Path) -> list[store.StoreSource]:
    collection = {
        "type": "FeatureCollection",
        "name": "edge-cases",
        "metadata": {"license": "CC BY 4.0", "retrieved_at": "2026-07-01T00:00:00Z", "source_updated_at": "2026-06-01"},
        "features": EDGE_FEATURES,
    }
    (root / "data").mkdir(parents=True, exist_ok=True)
    (root / "data/edge.geojson").write_text(json.dumps(collection, ensure_ascii=False), encoding="utf-8")
    (root / "data/summary.json").write_text(json.dumps({"answer": 42}), encoding="utf-8")
    return [
        store.StoreSource("edge", "data/edge.geojson", "features", "FL", "observed"),
        store.StoreSource("summary", "data/summary.json", "document", "AL", "observed"),
    ]


def test_two_builds_from_unchanged_inputs_are_byte_identical(tmp_path: Path) -> None:
    sources = write_fixture_root(tmp_path)
    first = tmp_path / "first.sqlite"
    second = tmp_path / "second.sqlite"

    store.build_store(tmp_path, first, sources)
    store.build_store(tmp_path, second, sources)

    assert first.read_bytes() == second.read_bytes()


def test_window_query_matches_the_serving_scan_on_the_fixture(tmp_path: Path) -> None:
    sources = write_fixture_root(tmp_path)
    target = tmp_path / "store.sqlite"
    store.build_store(tmp_path, target, sources)

    windows = [
        (0.0, 0.0, 1.0, 1.0),  # straddle touches the edge exactly
        (4.0, 4.0, 5.0, 5.0),  # inside the diagonal's bbox but off its geometry
        (7.9, 7.9, 9.0, 9.0),  # second part of the multi-part geometry only
        (100.0, 100.0, 101.0, 101.0),  # matches nothing
        (-10.0, -10.0, 10.0, 10.0),  # everything with coordinates
    ]
    connection = store.open_store(target)
    try:
        for window in windows:
            expected = [
                index
                for index, feature in enumerate(EDGE_FEATURES)
                if scan_intersects(feature.get("geometry"), window)
            ]
            got = [ordinal for ordinal, _ in store.window_features(connection, "edge", window)]
            assert got == expected, window
    finally:
        connection.close()

    # The scan's semantics are pinned deliberately: bbox intersection, not
    # true geometry intersection. The middle window misses every drawn shape,
    # yet matches both the diagonal (its bbox interior) and the multi-part
    # feature (whose single bbox spans the gap between its parts).
    assert [
        index
        for index, feature in enumerate(EDGE_FEATURES)
        if scan_intersects(feature.get("geometry"), (4.0, 4.0, 5.0, 5.0))
    ] == [1, 2]


def test_window_query_matches_the_serving_scan_on_a_real_mlit_dataset(tmp_path: Path) -> None:
    relative = ALL_DATASETS["railway"]
    source_path = tmp_path / relative
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_bytes((PROJECT_ROOT / relative).read_bytes())
    target = tmp_path / "store.sqlite"
    store.build_store(tmp_path, target, [store.StoreSource("railway", relative, "features", "FL", "observed")])

    features = json.loads(source_path.read_text(encoding="utf-8"))["features"]
    connection = store.open_store(target)
    try:
        for window in [
            (139.58, 35.44, 139.60, 35.46),
            (140.2757, 35.4387, 140.2913, 35.4513),
            (139.0, 35.0, 141.0, 36.0),
        ]:
            expected = [
                index
                for index, feature in enumerate(features)
                if scan_intersects(feature.get("geometry"), window)
            ]
            got = [ordinal for ordinal, _ in store.window_features(connection, "railway", window)]
            assert got == expected, window
        stored = store.window_features(connection, "railway", (139.0, 35.0, 141.0, 36.0))
        assert json.loads(stored[0][1]) == features[stored[0][0]]
    finally:
        connection.close()


def test_manifest_detects_source_drift_and_a_corrupted_store(tmp_path: Path) -> None:
    sources = write_fixture_root(tmp_path)
    target = tmp_path / "store.sqlite"
    store.build_store(tmp_path, target, sources)
    assert store.verify_store(tmp_path, target, expected_keys=[source.key for source in sources]) == []

    (tmp_path / "data/summary.json").write_text(json.dumps({"answer": 43}), encoding="utf-8")
    failures = store.verify_store(tmp_path, target)
    assert any("drifted" in failure and "summary" in failure for failure in failures)

    writable = sqlite3.connect(target)
    writable.execute("DELETE FROM features WHERE dataset_key = 'edge' AND ordinal = 0")
    writable.commit()
    writable.close()
    failures = store.verify_store(tmp_path, target)
    assert any("manifest says 4 features, store holds 3" in failure for failure in failures)


def test_missing_tables_report_as_corruption_failures_not_exceptions(tmp_path: Path) -> None:
    sources = write_fixture_root(tmp_path)
    target = tmp_path / "store.sqlite"
    store.build_store(tmp_path, target, sources)

    writable = sqlite3.connect(target)
    writable.execute("DROP TABLE features")
    writable.commit()
    writable.close()

    failures = store.verify_store(tmp_path, target)
    assert any("store is corrupt" in failure for failure in failures)


def test_schema_version_mismatch_means_rebuild_not_migrate(tmp_path: Path) -> None:
    sources = write_fixture_root(tmp_path)
    target = tmp_path / "store.sqlite"
    store.build_store(tmp_path, target, sources)

    writable = sqlite3.connect(target)
    writable.execute("PRAGMA user_version = 999")
    writable.commit()
    writable.close()

    with pytest.raises(store.StoreVersionError, match="rebuild"):
        store.open_store(target)
    failures = store.verify_store(tmp_path, target)
    assert any("999" in failure for failure in failures)


def test_envelope_preserves_every_top_level_member_in_source_order(tmp_path: Path) -> None:
    sources = write_fixture_root(tmp_path)
    target = tmp_path / "store.sqlite"
    store.build_store(tmp_path, target, sources)

    connection = store.open_store(target)
    try:
        envelope_json, tier, evidence_state, retrieved_at = connection.execute(
            "SELECT envelope_json, tier, evidence_state, retrieved_at FROM datasets WHERE key = 'edge'"
        ).fetchone()
    finally:
        connection.close()
    envelope = json.loads(envelope_json)
    assert list(envelope) == ["type", "name", "metadata", "features"]
    assert envelope["features"] == []
    assert envelope["metadata"]["license"] == "CC BY 4.0"
    assert (tier, evidence_state, retrieved_at) == ("FL", "observed", "2026-07-01T00:00:00Z")


def test_every_service_dataset_has_a_store_source_and_the_path_is_gitignored() -> None:
    sources = store_sources()
    keys = {source.key for source in sources}
    assert set(ALL_DATASETS) <= keys
    assert {"sceneCatalog", "sceneHandoff:uc24_16_nihonbashi", "sceneHandoff:uc24_13_sapporo"} <= keys
    assert all(source.tier in store.TIERS and source.evidence_state in store.EVIDENCE_STATES for source in sources)

    ignored = subprocess.run(
        ["git", "check-ignore", "-q", store.STORE_PATH],
        cwd=PROJECT_ROOT,
        check=False,
    )
    assert ignored.returncode == 0, "the store file must be gitignored"
