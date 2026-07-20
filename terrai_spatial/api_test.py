from __future__ import annotations

import pytest

from terrai_spatial.api import app


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
