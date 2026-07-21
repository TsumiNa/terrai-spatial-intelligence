from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from terrai_spatial.api import app
from terrai_spatial.data_service import ROOT, service


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/health",
        "/api/v1/catalog",
        "/api/v1/bootstrap",
        "/api/v1/datasets/{key}",
        "/api/v1/features/{key}",
        "/api/v1/recommendations/{analysis}",
        "/api/v1/scenes",
        "/api/v1/scenes/{scene_id}",
    ],
)
def test_fastapi_exposes_health_data_query_and_analysis_routes(path: str) -> None:
    assert path in {getattr(route, "path", None) for route in app.routes}


def test_packaged_data_is_mounted_where_the_frontend_expects_tiles() -> None:
    mounts = {getattr(route, "path", None) for route in app.routes if hasattr(route, "app")}
    assert "/api/v1/assets" in mounts


def run_lifespan() -> None:
    async def boot() -> None:
        async with app.router.lifespan_context(app):
            pass

    asyncio.run(boot())


def test_startup_refuses_to_serve_without_the_store(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(service, "root", tmp_path)
    with pytest.raises(RuntimeError, match="spatial store is missing"):
        run_lifespan()


def test_startup_verifies_the_store_against_its_sources() -> None:
    run_lifespan()


def test_committed_openapi_schema_matches_the_live_application() -> None:
    """The TypeScript client is generated from webapp/openapi.json; a route or
    response-model change without regeneration must fail here, not in review."""

    committed = json.loads((ROOT / "webapp" / "openapi.json").read_text(encoding="utf-8"))
    assert committed == app.openapi(), (
        "webapp/openapi.json is stale; run `npm run generate:api` in webapp/"
    )
