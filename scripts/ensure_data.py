#!/usr/bin/env python3
"""Inspect, reconstruct or update TerrAI data using the same tasks as startup."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from terrai_spatial.data_tasks import TASKS, ensure_data, status_rows  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("status", "ensure", "update"), nargs="?", default="ensure")
    parser.add_argument("--only", choices=tuple(TASKS), action="append", help="limit work to one or more tasks")
    parser.add_argument("--offline", action="store_true", help="do not download missing remote data")
    args = parser.parse_args()
    if args.action == "status":
        for state in status_rows():
            print(f"{state.name:10} {state.status:8} {state.reason}")
        return
    try:
        ensure_data(selected=args.only, allow_network=not args.offline, force=args.action == "update")
    except (RuntimeError, subprocess.CalledProcessError) as error:
        print(f"TerrAI data error: {error}", file=sys.stderr)
        raise SystemExit(2) from error


if __name__ == "__main__":
    main()
