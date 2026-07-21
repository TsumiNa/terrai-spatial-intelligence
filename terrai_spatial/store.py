"""The spatially indexed SQLite store: schema, deterministic build, verification.

One gitignored database file holds every dataset the service exposes —
feature collections in ``features`` with an R-tree over per-feature bounding
boxes, whole-document JSON products in ``documents``, and a ``datasets``
manifest row per key tying store content to source file hashes. The committed
GeoJSON stays the canonical interchange and provenance format; this store is
a derived artifact rebuilt by ``ensure_data``.

Design commitments (see docs/refactor/data-pipeline-and-store/02-spatial-store-pr2.md):

- **Derived, never migrated.** ``PRAGMA user_version`` carries the schema
  version; a mismatch at open means rebuild. There are no migration files for
  a rebuildable artifact.
- **Deterministic.** Two builds from unchanged inputs are byte-identical. No
  wall-clock value enters the store; the ``built_at`` stamp is the newest
  source file's modification time, which is stable between consecutive
  builds and still answers "what data state is this store built from".
- **Hand-written SQL, no ORM.** Every statement is a named constant so the
  eventual Postgres pairing is a file diff.
- **Exact bbox semantics.** SQLite's R-tree stores 32-bit floats rounded
  outward, so it serves as a conservative prefilter only; the float64 bbox
  columns on ``features`` decide intersection exactly, matching the
  behaviour of the ``_intersects_bbox`` scan it replaces.
- **FL/SL/AL is schema.** Every dataset row carries its tier and evidence
  state. The SL extension — a ``model_runs`` table (model, version, inputs
  hash, scenario, run timestamp) whose prediction sets enter ``features`` as
  ``SL``-tier datasets referencing their run — is designed here and
  deliberately not created until the first integrated SL output exists.

The store file lives outside ``data/`` so the static ``/api/v1/assets`` mount
never serves it.
"""

from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Sequence

from .pipeline.io import file_sha256


STORE_PATH = "var/store/terrai.sqlite"
SCHEMA_VERSION = 1

TIERS = ("FL", "SL", "AL")
EVIDENCE_STATES = ("observed", "synthetic", "unresolved")

CREATE_DATASETS = """
CREATE TABLE datasets (
    key TEXT PRIMARY KEY,
    kind TEXT NOT NULL CHECK (kind IN ('features', 'document')),
    tier TEXT NOT NULL CHECK (tier IN ('FL', 'SL', 'AL')),
    evidence_state TEXT NOT NULL CHECK (evidence_state IN ('observed', 'synthetic', 'unresolved')),
    source_path TEXT NOT NULL,
    source_sha256 TEXT NOT NULL,
    source_crs TEXT,
    license TEXT,
    retrieved_at TEXT,
    source_updated_at TEXT,
    feature_count INTEGER,
    min_x REAL, min_y REAL, max_x REAL, max_y REAL,
    envelope_json TEXT,
    built_at TEXT NOT NULL
) STRICT
"""

CREATE_FEATURES = """
CREATE TABLE features (
    dataset_key TEXT NOT NULL REFERENCES datasets(key),
    ordinal INTEGER NOT NULL,
    feature_json TEXT NOT NULL,
    min_x REAL, min_y REAL, max_x REAL, max_y REAL,
    PRIMARY KEY (dataset_key, ordinal)
)
"""

CREATE_FEATURES_RTREE = """
CREATE VIRTUAL TABLE features_rtree USING rtree(id, min_x, max_x, min_y, max_y)
"""

CREATE_DOCUMENTS = """
CREATE TABLE documents (
    key TEXT PRIMARY KEY,
    document_json TEXT NOT NULL
) STRICT
"""

INSERT_DATASET = """
INSERT INTO datasets (
    key, kind, tier, evidence_state, source_path, source_sha256, source_crs,
    license, retrieved_at, source_updated_at, feature_count,
    min_x, min_y, max_x, max_y, envelope_json, built_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

INSERT_FEATURE = """
INSERT INTO features (dataset_key, ordinal, feature_json, min_x, min_y, max_x, max_y)
VALUES (?, ?, ?, ?, ?, ?, ?)
"""

INSERT_FEATURE_RTREE = """
INSERT INTO features_rtree (id, min_x, max_x, min_y, max_y)
SELECT rowid, min_x, max_x, min_y, max_y FROM features WHERE min_x IS NOT NULL
"""

INSERT_DOCUMENT = "INSERT INTO documents (key, document_json) VALUES (?, ?)"

# The R-tree join is a conservative float32 prefilter; the float64 columns on
# `features` decide intersection exactly, preserving the scan's semantics.
WINDOW_QUERY = """
SELECT f.ordinal, f.feature_json
FROM features f
JOIN features_rtree r ON r.id = f.rowid
WHERE f.dataset_key = ?
  AND r.max_x >= ? AND r.min_x <= ? AND r.max_y >= ? AND r.min_y <= ?
  AND f.max_x >= ? AND f.min_x <= ? AND f.max_y >= ? AND f.min_y <= ?
ORDER BY f.ordinal
"""


class StoreVersionError(RuntimeError):
    """The store's schema version does not match; rebuild it, never migrate."""


@dataclass(frozen=True)
class StoreSource:
    """One dataset the build ingests, assembled by the build script."""

    key: str
    path: str
    kind: str  # 'features' | 'document'
    tier: str
    evidence_state: str


def _require_rtree() -> None:
    probe = sqlite3.connect(":memory:")
    try:
        probe.execute("CREATE VIRTUAL TABLE probe USING rtree(id, min_x, max_x, min_y, max_y)")
    except sqlite3.OperationalError as error:  # pragma: no cover - platform-dependent
        raise RuntimeError(
            "this Python's SQLite lacks the R-tree module (SQLITE_ENABLE_RTREE); "
            "install a standard CPython build to create the spatial store"
        ) from error
    finally:
        probe.close()


def _coordinate_pairs(value: Any) -> Iterable[tuple[float, float]]:
    if isinstance(value, list) and len(value) >= 2 and all(isinstance(item, (int, float)) for item in value[:2]):
        yield float(value[0]), float(value[1])
        return
    if isinstance(value, list):
        for item in value:
            yield from _coordinate_pairs(item)


def feature_bbox(geometry: dict[str, Any] | None) -> tuple[float, float, float, float] | None:
    """One vertex walk per feature, at build time — the walk the serving scan
    used to repeat per feature per query."""

    if not geometry:
        return None
    pairs = list(_coordinate_pairs(geometry.get("coordinates")))
    if not pairs:
        return None
    return (
        min(x for x, _ in pairs),
        min(y for _, y in pairs),
        max(x for x, _ in pairs),
        max(y for _, y in pairs),
    )


def _source_stamp(value: dict[str, Any]) -> tuple[str | None, str | None, str | None]:
    """(license, retrieved_at, source_updated_at) from embedded metadata, verbatim."""

    metadata = value.get("metadata") if isinstance(value.get("metadata"), dict) else value
    return (
        metadata.get("license") if isinstance(metadata.get("license"), str) else None,
        metadata.get("retrieved_at") if isinstance(metadata.get("retrieved_at"), str) else None,
        metadata.get("source_updated_at") if isinstance(metadata.get("source_updated_at"), str) else None,
    )


def _built_at(root: Path, sources: Sequence[StoreSource]) -> str:
    newest = max((root / source.path).stat().st_mtime for source in sources)
    return datetime.fromtimestamp(newest, tz=UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_store(root: Path, target: Path, sources: Sequence[StoreSource]) -> dict[str, int]:
    """Build the store atomically: temp path, validate, rename over the old one."""

    _require_rtree()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".build")
    temporary.unlink(missing_ok=True)
    built_at = _built_at(root, sources)

    connection = sqlite3.connect(temporary)
    try:
        connection.execute("PRAGMA journal_mode = MEMORY")
        connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        connection.execute(CREATE_DATASETS)
        connection.execute(CREATE_FEATURES)
        connection.execute(CREATE_DOCUMENTS)
        connection.execute(CREATE_FEATURES_RTREE)

        counts = {"features": 0, "documents": 0}
        for source in sorted(sources, key=lambda item: item.key):
            path = root / source.path
            value = json.loads(path.read_text(encoding="utf-8"))
            sha256 = file_sha256(path)
            if source.kind == "features":
                if not isinstance(value, dict) or value.get("type") != "FeatureCollection":
                    raise RuntimeError(f"{source.key} is not a GeoJSON FeatureCollection: {source.path}")
                features = value.get("features", [])
                rows = []
                dataset_bbox: list[float] | None = None
                for ordinal, feature in enumerate(features):
                    bbox = feature_bbox(feature.get("geometry"))
                    rows.append(
                        (
                            source.key,
                            ordinal,
                            json.dumps(feature, ensure_ascii=False, separators=(",", ":")),
                            *(bbox if bbox else (None, None, None, None)),
                        )
                    )
                    if bbox:
                        if dataset_bbox is None:
                            dataset_bbox = list(bbox)
                        else:
                            dataset_bbox = [
                                min(dataset_bbox[0], bbox[0]),
                                min(dataset_bbox[1], bbox[1]),
                                max(dataset_bbox[2], bbox[2]),
                                max(dataset_bbox[3], bbox[3]),
                            ]
                connection.executemany(INSERT_FEATURE, rows)
                envelope = {name: ([] if name == "features" else item) for name, item in value.items()}
                license_text, retrieved_at, source_updated_at = _source_stamp(value)
                connection.execute(
                    INSERT_DATASET,
                    (
                        source.key,
                        "features",
                        source.tier,
                        source.evidence_state,
                        source.path,
                        sha256,
                        "EPSG:4326",
                        license_text,
                        retrieved_at,
                        source_updated_at,
                        len(features),
                        *(dataset_bbox if dataset_bbox else (None, None, None, None)),
                        json.dumps(envelope, ensure_ascii=False, separators=(",", ":")),
                        built_at,
                    ),
                )
                counts["features"] += len(features)
            else:
                if not isinstance(value, dict):
                    raise RuntimeError(f"{source.key} document root is not an object: {source.path}")
                connection.execute(
                    INSERT_DOCUMENT,
                    (source.key, json.dumps(value, ensure_ascii=False, separators=(",", ":"))),
                )
                license_text, retrieved_at, source_updated_at = _source_stamp(value)
                connection.execute(
                    INSERT_DATASET,
                    (
                        source.key,
                        "document",
                        source.tier,
                        source.evidence_state,
                        source.path,
                        sha256,
                        None,
                        license_text,
                        retrieved_at,
                        source_updated_at,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        built_at,
                    ),
                )
                counts["documents"] += 1
        connection.execute(INSERT_FEATURE_RTREE)
        connection.commit()
    finally:
        connection.close()

    failures = verify_store(root, temporary, expected_keys=[source.key for source in sources])
    if failures:
        temporary.unlink(missing_ok=True)
        raise RuntimeError("built store failed validation: " + "; ".join(failures))
    os.replace(temporary, target)
    return counts


def open_store(path: Path) -> sqlite3.Connection:
    """Read-only connection; a schema version mismatch means rebuild."""

    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        version = connection.execute("PRAGMA user_version").fetchone()[0]
    except sqlite3.Error:
        connection.close()
        raise
    if version != SCHEMA_VERSION:
        connection.close()
        raise StoreVersionError(
            f"store schema version is {version}, expected {SCHEMA_VERSION}; "
            "rebuild it with: uv run python -m terrai_spatial data ensure --only store"
        )
    return connection


def window_features(connection: sqlite3.Connection, key: str, bbox: tuple[float, float, float, float]) -> list[tuple[int, str]]:
    """(ordinal, feature_json) rows whose bbox intersects the window, in source order."""

    west, south, east, north = bbox
    return connection.execute(
        WINDOW_QUERY,
        (key, west, east, south, north, west, east, south, north),
    ).fetchall()


def verify_store(root: Path, path: Path, *, expected_keys: Sequence[str] | None = None) -> list[str]:
    """Drift and integrity report: source hashes, counts, index coverage."""

    failures: list[str] = []
    try:
        connection = open_store(path)
    except StoreVersionError as error:
        return [str(error)]
    except sqlite3.Error as error:
        return [f"store cannot be opened: {error}"]
    try:
        # This runs inside `terrai validate`: any corruption must come back
        # as a readable failure string, never as an exception.
        rows = connection.execute(
            "SELECT key, kind, source_path, source_sha256, feature_count FROM datasets ORDER BY key"
        ).fetchall()
        by_key = {row[0]: row for row in rows}
        for expected in expected_keys or []:
            if expected not in by_key:
                failures.append(f"dataset missing from the store: {expected}")
        for key, kind, source_path, source_sha256, feature_count in rows:
            source = root / source_path
            if not source.is_file():
                failures.append(f"{key}: source file is missing: {source_path}")
                continue
            if file_sha256(source) != source_sha256:
                failures.append(f"{key}: source file drifted from the store: {source_path}")
            if kind == "features":
                stored = connection.execute(
                    "SELECT COUNT(*) FROM features WHERE dataset_key = ?", (key,)
                ).fetchone()[0]
                if stored != feature_count:
                    failures.append(f"{key}: manifest says {feature_count} features, store holds {stored}")
        indexed = connection.execute("SELECT COUNT(*) FROM features_rtree").fetchone()[0]
        with_bbox = connection.execute("SELECT COUNT(*) FROM features WHERE min_x IS NOT NULL").fetchone()[0]
        if indexed != with_bbox:
            failures.append(f"R-tree indexes {indexed} features; {with_bbox} carry a bounding box")
    except sqlite3.Error as error:
        failures.append(f"store is corrupt: {error}")
    finally:
        connection.close()
    return failures
