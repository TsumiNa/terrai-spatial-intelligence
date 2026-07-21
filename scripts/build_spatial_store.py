"""Build the spatially indexed SQLite store from every service dataset."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from terrai_spatial.data_service import store_sources  # noqa: E402
from terrai_spatial.store import STORE_PATH, build_store  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="accepted for data-task compatibility")
    parser.parse_args()
    sources = store_sources()
    counts = build_store(ROOT, ROOT / STORE_PATH, sources)
    print(
        f"Spatial store ready: {len(sources)} datasets, "
        f"{counts['features']} features, {counts['documents']} documents at {STORE_PATH}"
    )


if __name__ == "__main__":
    main()
