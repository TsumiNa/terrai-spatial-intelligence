from __future__ import annotations

import re
from datetime import UTC, datetime

import pytest

from terrai_spatial.pipeline import provenance


def test_new_stamps_are_second_resolution_z_suffixed_utc() -> None:
    stamp = provenance.utc_timestamp()

    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", stamp)
    parsed = provenance.parse_timestamp(stamp)
    assert parsed.tzinfo is not None
    assert abs((datetime.now(tz=UTC) - parsed).total_seconds()) < 60


def test_parser_accepts_all_three_committed_spellings() -> None:
    z_suffixed = provenance.parse_timestamp("2026-07-21T17:00:00Z")
    offset = provenance.parse_timestamp("2026-07-21T17:00:00+00:00")
    date_only = provenance.parse_timestamp("2026-07-21")

    assert z_suffixed == offset
    assert date_only == datetime(2026, 7, 21, tzinfo=UTC)
    assert z_suffixed.date() == date_only.date()


def test_parser_rejects_non_timestamps() -> None:
    with pytest.raises(ValueError, match="unrecognized provenance timestamp"):
        provenance.parse_timestamp("current download; map-sheet vintage varies")
