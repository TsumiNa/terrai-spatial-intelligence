from __future__ import annotations

import unittest

from terrai_spatial.api import app


class ExhibitionApiTests(unittest.TestCase):
    def test_fastapi_exposes_health_data_query_and_analysis_routes(self) -> None:
        paths = {route.path for route in app.routes}
        for path in (
            "/api/v1/health",
            "/api/v1/catalog",
            "/api/v1/bootstrap",
            "/api/v1/datasets/{key}",
            "/api/v1/features/{key}",
            "/api/v1/recommendations/{analysis}",
        ):
            self.assertIn(path, paths)

    def test_packaged_data_is_mounted_where_the_frontend_expects_tiles(self) -> None:
        mounts = {route.path for route in app.routes if hasattr(route, "app")}
        self.assertIn("/api/v1/assets", mounts)


if __name__ == "__main__":
    unittest.main()
