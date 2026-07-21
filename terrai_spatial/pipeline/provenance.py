"""The provenance timestamp: one producer format, one tolerant parser.

Committed data carries three spellings from before this module existed —
Z-suffixed ISO (``2026-07-21T17:00:00Z``), offset ISO
(``2026-07-21T17:00:00+00:00``) and plain dates (``2026-07-20``). New stamps
use the Z-suffixed form only; the parser accepts all three because consumers
must keep reading the committed history.
"""

from __future__ import annotations

from datetime import UTC, datetime


def utc_timestamp() -> str:
    """Second-resolution UTC timestamp, Z-suffixed."""

    return datetime.now(tz=UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_timestamp(value: str) -> datetime:
    """Parse any committed ``retrieved_at`` spelling into an aware datetime.

    Date-only strings parse to midnight UTC.
    """

    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as error:
        raise ValueError(f"unrecognized provenance timestamp: {value!r}") from error
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed
