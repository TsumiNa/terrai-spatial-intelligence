from __future__ import annotations

import unittest

from terrai_spatial.data_service import DATASETS, DatasetNotFoundError, service


class DataServiceTests(unittest.TestCase):
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

    def test_unknown_dataset_key_is_rejected(self) -> None:
        with self.assertRaises(DatasetNotFoundError):
            service.load("no-such-dataset")

    def test_feature_query_rejects_a_dataset_that_is_not_a_feature_collection(self) -> None:
        with self.assertRaisesRegex(ValueError, "not a GeoJSON FeatureCollection"):
            service.query_features("jointSummary")


if __name__ == "__main__":
    unittest.main()
