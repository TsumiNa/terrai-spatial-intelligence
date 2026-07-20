#!/usr/bin/env python3
"""Fetch the local-only TEPCO source cache when needed, then rebuild its screen."""

from __future__ import annotations

import argparse
import os

from fetch_tepco_grid import DEFAULT_URL, fetch_tepco_data
from parse_tepco_grid import main as parse_grid


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="refresh the official ZIP before parsing")
    parser.add_argument("--offline", action="store_true", help="use only an existing local ZIP/CSV cache")
    parser.add_argument("--url", default=os.environ.get("TERRAI_TEPCO_CHIBA_URL", DEFAULT_URL))
    args = parser.parse_args()
    fetch_tepco_data(url=args.url, force=args.force, offline=args.offline)
    parse_grid()


if __name__ == "__main__":
    main()
