from __future__ import annotations

import unittest

from terrai_spatial.api import app
from terrai_spatial.data_service import DATASETS, service


class ExhibitionApiTests(unittest.TestCase):
    def test_health_reports_all_file_backed_datasets_ready(self) -> None:
        health = service.health()
        self.assertEqual(health["status"], "ready")
        self.assertEqual(health["datasets_ready"], len(DATASETS))
        self.assertEqual(health["datasets_total"], len(DATASETS))

    def test_bootstrap_contains_ranked_server_side_recommendations(self) -> None:
        payload = service.bootstrap()
        self.assertEqual(payload["meta"]["api_version"], "v1")
        self.assertIn("facilitySummary", payload)
        slope = payload["recommendations"]["slope"]["features"]
        self.assertTrue(slope)
        scores = [feature["properties"]["risk_score"] for feature in slope]
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertTrue(all(feature["properties"]["risk_band"] == "high" for feature in slope))
        yokohama_evidence = payload["recommendations"]["embeddingYokohama"]["features"]
        mobara_evidence = payload["recommendations"]["embeddingMobara"]["features"]
        self.assertTrue(all(feature["properties"]["region"] == "yokohama" for feature in yokohama_evidence))
        self.assertTrue(all(feature["properties"]["region"] == "mobara" for feature in mobara_evidence))

    def test_feature_query_filters_sorts_and_limits(self) -> None:
        result = service.query_features(
            "solar",
            where="status",
            equals="preferred",
            sort="score",
            descending=True,
            limit=3,
        )
        self.assertEqual(result["query"]["returned"], 3)
        scores = [feature["properties"]["score"] for feature in result["features"]]
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertTrue(all(feature["properties"]["status"] == "preferred" for feature in result["features"]))

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


if __name__ == "__main__":
    unittest.main()
