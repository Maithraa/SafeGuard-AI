"""
Automated Test Suite for FraudGuard AI
Validates database integrity, ML inference, API endpoints, and live simulation.
"""

import unittest
import json
from app import app
from fraud_detection import detector


class FraudGuardTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()

    def test_ml_model_and_detector(self):
        """Test rule score, ML anomaly score, and XAI reasons."""
        # 1. High risk payload
        test_threat = {
            "transaction_id": "TEST-CRIT-001",
            "account_id": "ACC101",
            "amount": 85000.0,
            "avg_amount": 4500.0,
            "location": "Dubai",
            "prev_location": "Erode",
            "geo_velocity_kmh": 2850.0,
            "transaction_frequency": 8,
            "time_anomaly": 1,
            "new_device": 1,
            "time": "03:15 AM",
        }
        res = detector.evaluate_transaction(test_threat)
        self.assertGreaterEqual(res["hybrid_score"], 60.0)
        self.assertIn(res["risk_level"], ["HIGH", "CRITICAL"])
        self.assertGreaterEqual(len(res["xai_reasons"]), 3)

        # 2. Normal payload
        test_normal = {
            "transaction_id": "TEST-NORM-001",
            "account_id": "ACC103",
            "amount": 2500.0,
            "avg_amount": 15000.0,
            "location": "Chennai",
            "prev_location": "Chennai",
            "geo_velocity_kmh": 0.0,
            "transaction_frequency": 1,
            "time_anomaly": 0,
            "new_device": 0,
            "time": "02:30 PM",
        }
        res_norm = detector.evaluate_transaction(test_normal)
        self.assertLessEqual(res_norm["hybrid_score"], 40.0)

    def test_routes_status_code(self):
        """Test all frontend page routes return 200."""
        routes = [
            "/", "/login", "/dashboard", "/transactions",
            "/accounts", "/analytics", "/alerts", "/upload", "/settings"
        ]
        for r in routes:
            response = self.client.get(r)
            self.assertEqual(response.status_code, 200, f"Route {r} failed with status {response.status_code}")

    def test_api_dashboard(self):
        """Test /api/dashboard returns metrics and recent suspicious."""
        res = self.client.get("/api/dashboard")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn("metrics", data)
        self.assertIn("recent_suspicious", data)
        self.assertIn("hourly_trend", data)

    def test_api_simulate_transaction(self):
        """Test /api/simulate-transaction generates transaction and returns XAI."""
        res = self.client.post("/api/simulate-transaction")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data["success"])
        self.assertEqual(data["analysis"]["risk_level"], "CRITICAL")
        self.assertGreaterEqual(len(data["analysis"]["xai_reasons"]), 3)

    def test_api_auth(self):
        """Test admin authentication."""
        res = self.client.post("/api/login", json={
            "email": "admin@fraudguard.ai",
            "password": "admin123"
        })
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data["success"])


if __name__ == "__main__":
    unittest.main()
