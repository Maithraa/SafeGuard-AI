"""
FraudGuard AI - Machine Learning Engine
Implements scikit-learn Isolation Forest with StandardScaler for unsupervised
transaction anomaly detection.
"""

import os
import joblib
import numpy as np

MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model")
MODEL_PATH = os.path.join(MODEL_DIR, "isolation_forest.pkl")

FEATURE_NAMES = [
    "amount",
    "avg_amount",
    "amount_ratio",
    "transaction_frequency",
    "new_device",
    "location_change",
    "time_anomaly",
    "geo_velocity_kmh",
]


class FraudMLModel:
    def __init__(self, model_path=MODEL_PATH):
        self.model_path = model_path
        self.scaler = None
        self.model = None
        self.load_or_train()

    def _generate_synthetic_baseline(self, n_samples=3000):
        """
        Generates realistic baseline transaction data (both normal patterns and injected anomalies)
        to train the unsupervised Isolation Forest model.
        """
        np.random.seed(42)

        # 92% Normal Transactions
        n_normal = int(n_samples * 0.92)
        normal_avg_amount = np.random.uniform(500, 8000, n_normal)
        normal_ratio = np.random.uniform(0.2, 1.8, n_normal)
        normal_amount = normal_avg_amount * normal_ratio
        normal_freq = np.random.poisson(1.2, n_normal)
        normal_new_device = np.random.choice([0, 1], p=[0.94, 0.06], size=n_normal)
        normal_loc_change = np.random.choice([0, 1], p=[0.90, 0.10], size=n_normal)
        normal_time_anomaly = np.random.choice([0, 1], p=[0.93, 0.07], size=n_normal)
        normal_velocity = np.random.exponential(15.0, n_normal)  # typical local transit / stationary

        X_normal = np.column_stack([
            normal_amount,
            normal_avg_amount,
            normal_ratio,
            normal_freq,
            normal_new_device,
            normal_loc_change,
            normal_time_anomaly,
            normal_velocity,
        ])

        # 8% Fraud / Anomalous Transactions
        n_fraud = n_samples - n_normal
        fraud_avg_amount = np.random.uniform(1000, 6000, n_fraud)
        fraud_ratio = np.random.uniform(4.5, 25.0, n_fraud)
        fraud_amount = fraud_avg_amount * fraud_ratio
        fraud_freq = np.random.randint(5, 15, size=n_fraud)
        fraud_new_device = np.random.choice([0, 1], p=[0.2, 0.8], size=n_fraud)
        fraud_loc_change = np.random.choice([0, 1], p=[0.1, 0.9], size=n_fraud)
        fraud_time_anomaly = np.random.choice([0, 1], p=[0.25, 0.75], size=n_fraud)
        fraud_velocity = np.random.uniform(600, 2500, size=n_fraud)  # impossible velocity

        X_fraud = np.column_stack([
            fraud_amount,
            fraud_avg_amount,
            fraud_ratio,
            fraud_freq,
            fraud_new_device,
            fraud_loc_change,
            fraud_time_anomaly,
            fraud_velocity,
        ])

        X = np.vstack([X_normal, X_fraud])
        return X

    def train(self):
        """Train Isolation Forest and StandardScaler, then serialize to disk."""
        from sklearn.ensemble import IsolationForest
        from sklearn.preprocessing import StandardScaler

        print("[FraudGuard ML] Generating baseline dataset and training Isolation Forest...")
        X = self._generate_synthetic_baseline()

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        model = IsolationForest(
            n_estimators=150,
            contamination=0.08,
            max_samples="auto",
            random_state=42,
            n_jobs=-1,
        )
        model.fit(X_scaled)

        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        payload = {
            "model": model,
            "scaler": scaler,
            "features": FEATURE_NAMES,
            "score_min": -0.35,
            "score_max": 0.20,
        }
        joblib.dump(payload, self.model_path)
        self.model = model
        self.scaler = scaler
        print(f"[FraudGuard ML] Model successfully trained and saved to {self.model_path}")

    def load_or_train(self):
        """Loads serialized model if it exists, otherwise triggers auto-training."""
        if os.path.exists(self.model_path):
            try:
                payload = joblib.load(self.model_path)
                self.model = payload["model"]
                self.scaler = payload["scaler"]
            except Exception as e:
                print(f"[FraudGuard ML] Error loading model ({e}). Retraining...")
                self.train()
        else:
            self.train()

    def predict_anomaly(self, feature_dict):
        """
        Runs ML inference on a single feature dictionary.
        Returns:
            dict with:
                - ml_score: float normalized from 0 (completely normal) to 100 (severe anomaly)
                - is_anomaly: bool
                - raw_score: float decision function value
        """
        if self.model is None or self.scaler is None:
            self.load_or_train()

        features = [
            float(feature_dict.get("amount", 0.0)),
            float(feature_dict.get("avg_amount", 1000.0)),
            float(feature_dict.get("amount_ratio", 1.0)),
            float(feature_dict.get("transaction_frequency", 1.0)),
            float(feature_dict.get("new_device", 0)),
            float(feature_dict.get("location_change", 0)),
            float(feature_dict.get("time_anomaly", 0)),
            float(feature_dict.get("geo_velocity_kmh", 0.0)),
        ]

        X_raw = np.array([features])
        X_scaled = self.scaler.transform(X_raw)

        # Raw decision score: higher is normal, lower is anomalous
        raw_score = float(self.model.decision_function(X_scaled)[0])
        pred = int(self.model.predict(X_scaled)[0])  # 1: normal, -1: anomaly

        # Normalize raw_score to 0-100 where 100 is highest risk
        # Empirical decision function range: typically ~ -0.25 to +0.20
        # When raw_score is <= -0.20, score should approach 95-100
        # When raw_score is >= +0.15, score should approach 0-10
        norm_score = (0.16 - raw_score) / (0.16 - (-0.22)) * 100.0
        ml_score = max(5.0, min(99.0, norm_score))

        return {
            "ml_score": round(ml_score, 1),
            "is_anomaly": pred == -1,
            "raw_decision_score": round(raw_score, 4),
        }


# Global singleton instance
ml_service = FraudMLModel()
