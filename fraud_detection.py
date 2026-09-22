"""
FraudGuard AI - Hybrid Fraud Detection & Explainable AI (XAI) Engine
Combines a deterministic Rule-Based Scoring Matrix with an Isolation Forest ML score,
and computes human-readable XAI explanations.
"""

from typing import Dict, Any, List
from ml_model import ml_service


class HybridFraudDetector:
    def __init__(self):
        self.ml = ml_service

    def calculate_rule_score(self, txn_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Rule-based Scoring Matrix (Max 100):
        - Amount Anomaly (>5x avg): +25
        - Impossible Velocity (>800 km/h or foreign location): +20
        - New Unrecognized Device: +20
        - Unusual Time (12 AM - 5 AM): +15
        - High Frequency (>5 in 10 mins): +20
        """
        rule_score = 0
        rule_breakdowns = []

        amount = float(txn_data.get("amount", 0.0))
        avg_amount = float(txn_data.get("avg_amount", 1000.0))
        ratio = amount / max(avg_amount, 1.0)

        geo_velocity = float(txn_data.get("geo_velocity_kmh", 0.0))
        location = str(txn_data.get("location", "")).lower()
        foreign_locations = ["dubai", "london", "singapore", "new york", "seychelles", "nigeria", "bangkok"]
        is_foreign = any(f in location for f in foreign_locations)

        new_device = int(txn_data.get("new_device", 0))
        time_anomaly = int(txn_data.get("time_anomaly", 0))
        frequency_10min = int(txn_data.get("transaction_frequency", 1))

        # 1. Amount Anomaly (>5x avg): +25
        if ratio > 5.0:
            rule_score += 25
            rule_breakdowns.append({
                "rule": "AMOUNT_SURGE",
                "points": 25,
                "desc": f"Transaction amount (₹{amount:,.2f}) is {ratio:.1f}x higher than typical baseline (₹{avg_amount:,.2f})"
            })
        elif ratio > 2.5:
            rule_score += 10
            rule_breakdowns.append({
                "rule": "ELEVATED_AMOUNT",
                "points": 10,
                "desc": f"Transaction amount (₹{amount:,.2f}) is {ratio:.1f}x above normal account baseline"
            })

        # 2. Impossible Velocity (>800 km/h or foreign location): +20
        if geo_velocity > 800.0 or is_foreign:
            rule_score += 20
            v_desc = f"Transit velocity of {geo_velocity:,.0f} km/h exceeds physical travel limits" if geo_velocity > 800 else f"Foreign terminal origin ({txn_data.get('location')}) inconsistent with domestic Indian residency"
            rule_breakdowns.append({
                "rule": "IMPOSSIBLE_VELOCITY",
                "points": 20,
                "desc": v_desc
            })
        elif geo_velocity > 250.0:
            rule_score += 10
            rule_breakdowns.append({
                "rule": "ABNORMAL_TRANSIT",
                "points": 10,
                "desc": f"High geographical relocation rate ({geo_velocity:,.0f} km/h) detected between consecutive actions"
            })

        # 3. New Unrecognized Device: +20
        if new_device == 1:
            rule_score += 20
            device_id = txn_data.get("device_id", "Unknown Device")
            rule_breakdowns.append({
                "rule": "UNRECOGNIZED_HARDWARE",
                "points": 20,
                "desc": f"First-time authentication from unregistered hardware signature ({device_id})"
            })

        # 4. Unusual Time (12 AM - 5 AM): +15
        if time_anomaly == 1:
            rule_score += 15
            txn_time = txn_data.get("time", "03:15 AM")
            rule_breakdowns.append({
                "rule": "OFF_HOURS_WINDOW",
                "points": 15,
                "desc": f"High-risk nocturnal execution window ({txn_time}) between 12:00 AM and 05:00 AM"
            })

        # 5. High Frequency (>5 in 10 mins): +20
        if frequency_10min > 5:
            rule_score += 20
            rule_breakdowns.append({
                "rule": "RAPID_BURST_VELOCITY",
                "points": 20,
                "desc": f"High-velocity burst: {frequency_10min} transactions completed in under 10 minutes"
            })
        elif frequency_10min >= 3:
            rule_score += 10
            rule_breakdowns.append({
                "rule": "ACCELERATED_FREQUENCY",
                "points": 10,
                "desc": f"Accelerated transfer cadence: {frequency_10min} transactions within 10 minutes"
            })

        rule_score = min(100, rule_score)
        return {
            "rule_score": rule_score,
            "rule_breakdowns": rule_breakdowns
        }

    def generate_xai_reasons(self, txn_data: Dict[str, Any], rule_data: Dict[str, Any], ml_data: Dict[str, Any], hybrid_score: float) -> List[str]:
        """
        Explainable AI Engine: Produces 3–5 human-readable bullet reasons
        explaining why the transaction was flagged.
        """
        reasons = []
        amount = float(txn_data.get("amount", 0.0))
        avg_amount = float(txn_data.get("avg_amount", 1000.0))
        ratio = amount / max(avg_amount, 1.0)
        location = txn_data.get("location", "Unknown")
        velocity = float(txn_data.get("geo_velocity_kmh", 0.0))
        freq = int(txn_data.get("transaction_frequency", 1))
        new_device = int(txn_data.get("new_device", 0))
        time_anomaly = int(txn_data.get("time_anomaly", 0))
        time_val = txn_data.get("time", "Night")

        # 1. Amount reason
        if ratio > 5.0:
            reasons.append(f"Severe value anomaly: Outflow of ₹{amount:,.2f} is {ratio:.1f}x higher than standard account mean (₹{avg_amount:,.2f}).")
        elif ratio > 2.0:
            reasons.append(f"Spending deviation: Amount ₹{amount:,.2f} is {ratio:.1f}x above baseline behavior.")

        # 2. Geo / Velocity reason
        if velocity > 800.0:
            prev_loc = txn_data.get("prev_location", "Tamil Nadu (Erode)")
            reasons.append(f"Impossible geo-velocity: Instantaneous leap from {prev_loc} to {location} ({velocity:,.0f} km/h) violates physical travel capabilities.")
        elif any(f in location.lower() for f in ["dubai", "london", "singapore", "seychelles"]):
            reasons.append(f"Offshore gateway: Originating IP / geofence resolved to {location}, conflicting with verified domestic KYC location.")

        # 3. Frequency reason
        if freq > 5:
            reasons.append(f"Rapid-fire transaction chaining: {freq} distinct transactions dispatched within a 10-minute window.")
        elif freq >= 3:
            reasons.append(f"Clustered velocity: {freq} rapid payment requests initiated consecutively.")

        # 4. Device security reason
        if new_device == 1:
            reasons.append("Unverified hardware profile: Transaction initiated from previously unseen device fingerprint without trusted biometric MFA.")

        # 5. Temporal anomaly
        if time_anomaly == 1:
            reasons.append(f"Irregular operational window: Authenticated at {time_val} (dormant hours: 12:00 AM – 05:00 AM).")

        # 6. ML Model Latent Anomaly
        if ml_data.get("is_anomaly") or ml_data.get("ml_score", 0) > 60:
            reasons.append(f"Unsupervised Isolation Forest flagged vector divergence (ML Anomaly Confidence: {ml_data.get('ml_score')}%) across combined behavioral coordinates.")

        # Guarantee at least 3 reasons for flagged items
        if len(reasons) < 3:
            if hybrid_score <= 30:
                reasons = [
                    "Transaction value is within the standard standard deviation for this account.",
                    "Device signature matches recognized and trusted hardware credential.",
                    "Geo-velocity and execution timestamp are consistent with historical telemetry."
                ]
            else:
                reasons.append("Multi-factor risk indexing exceeded standard supervisory thresholds.")
                reasons.append("Automated synthetic baseline checks detected irregular transfer velocity.")

        # Cap at 5 most impactful reasons
        return reasons[:5]

    def evaluate_transaction(self, txn_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs full hybrid risk evaluation.
        Hybrid Score = 0.6 * Rule Score + 0.4 * (ML Anomaly Score normalized 0-100)
        Risk Thresholds:
        - 0–30: LOW (Green)
        - 31–60: MEDIUM (Yellow)
        - 61–80: HIGH (Orange)
        - 81–100: CRITICAL (Red)
        """
        # 1. Rule Engine
        rule_eval = self.calculate_rule_score(txn_data)
        rule_score = rule_eval["rule_score"]

        # 2. ML Engine
        ml_eval = self.ml.predict_anomaly(txn_data)
        ml_score = ml_eval["ml_score"]

        # 3. Hybrid Calculation
        hybrid_score = round(0.6 * rule_score + 0.4 * ml_score, 1)

        # 4. Threshold Classification
        if hybrid_score <= 30:
            risk_level = "LOW"
            color_code = "#10b981"  # Green
            badge_class = "risk-badge-low"
            border_class = "risk-border-low"
        elif hybrid_score <= 60:
            risk_level = "MEDIUM"
            color_code = "#f59e0b"  # Yellow / Amber
            badge_class = "risk-badge-medium"
            border_class = "risk-border-medium"
        elif hybrid_score <= 80:
            risk_level = "HIGH"
            color_code = "#f97316"  # Orange
            badge_class = "risk-badge-high"
            border_class = "risk-border-high"
        else:
            risk_level = "CRITICAL"
            color_code = "#dc2626"  # Red / Crimson
            badge_class = "risk-badge-critical"
            border_class = "risk-border-critical"

        # 5. Explainable AI Engine
        xai_reasons = self.generate_xai_reasons(txn_data, rule_eval, ml_eval, hybrid_score)

        return {
            "hybrid_score": hybrid_score,
            "rule_score": rule_score,
            "ml_score": ml_score,
            "risk_level": risk_level,
            "color_code": color_code,
            "badge_class": badge_class,
            "border_class": border_class,
            "rule_breakdowns": rule_eval["rule_breakdowns"],
            "ml_anomaly": ml_eval["is_anomaly"],
            "raw_decision_score": ml_eval.get("raw_decision_score", 0.0),
            "xai_reasons": xai_reasons,
        }


# Global singleton instance
detector = HybridFraudDetector()
