"""Export the FastAPI OpenAPI schema for TypeScript code generation.

Run from the repository root; `npm run generate:api` in `webapp/` does this via
`uv run --directory ..`. The committed `webapp/openapi.json` is the input to
`openapi-typescript`, and `terrai_spatial/api_test.py` fails whenever the
committed schema drifts from the live application.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT))

from terrai_spatial.api import app  # noqa: E402

output = Path(__file__).resolve().parents[1] / "openapi.json"
output.write_text(json.dumps(app.openapi(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"wrote {output}")
