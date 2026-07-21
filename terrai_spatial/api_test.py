from __future__ import annotations

import json

import pytest

from terrai_spatial.api import app
from terrai_spatial.data_service import ROOT


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/health",
        "/api/v1/catalog",
        "/api/v1/bootstrap",
        "/api/v1/datasets/{key}",
        "/api/v1/features/{key}",
        "/api/v1/recommendations/{analysis}",
    ],
)
def test_fastapi_exposes_health_data_query_and_analysis_routes(path: str) -> None:
    assert path in {getattr(route, "path", None) for route in app.routes}


def test_packaged_data_is_mounted_where_the_frontend_expects_tiles() -> None:
    mounts = {getattr(route, "path", None) for route in app.routes if hasattr(route, "app")}
    assert "/api/v1/assets" in mounts


def test_committed_openapi_schema_matches_the_live_application() -> None:
    """The TypeScript client is generated from webapp/openapi.json; a route or
    response-model change without regeneration must fail here, not in review."""

    committed = json.loads((ROOT / "webapp" / "openapi.json").read_text(encoding="utf-8"))
    assert committed == app.openapi(), (
        "webapp/openapi.json is stale; run `npm run generate:api` in webapp/"
    )
