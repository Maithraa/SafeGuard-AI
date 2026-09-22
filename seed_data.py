"""
FraudGuard AI - Seed Data Engine
Generates 50+ realistic records with Indian financial context (INR, UPI, NEFT, IMPS,
cities: Erode, Coimbatore, Chennai, Bangalore, Mumbai, Delhi, Dubai) and mule network loops.
"""

import hashlib
import json
from datetime import datetime, timedelta
import random

from database import init_db, get_db_connection
from fraud_detection import detector


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


LOCATIONS = ["Erode", "Coimbatore", "Chennai", "Bengaluru", "Mumbai", "Delhi", "Dubai"]
MERCHANTS = [
    ("Swiggy Foods", "UPI"),
    ("Flipkart India", "NetBanking"),
    ("Amazon Pay", "UPI"),
    ("TNEB Electricity Board", "NEFT"),
    ("Reliance Digital Erode", "POS Card"),
    ("Apollo Pharmacy Coimbatore", "UPI"),
    ("Croma Electronics Chennai", "Credit Card"),
    ("Zomato Delivery", "UPI"),
    ("Indian Oil Petrol Pump", "POS Card"),
    ("IRCTC Railway Booking", "NetBanking"),
    ("Dubai Gold & Diamond Park", "Wire Transfer"),
    ("Offshore Crypto Gateway", "P2P Transfer"),
    ("QuickCash ATM Erode", "ATM Withdrawal"),
    ("Blinkit Groceries", "UPI"),
    ("Tata Neu Superapp", "UPI"),
]

SAMPLE_ACCOUNTS = [
    ("ACC101", "Karthik Natarajan", "Savings", 4500.0, "Erode", "Active", 124500.0, "High Risk"),
    ("ACC102", "Priya Sundaram", "Savings", 3800.0, "Coimbatore", "Active", 84200.0, "Medium Risk"),
    ("ACC103", "Ramesh Kumar", "Current", 15000.0, "Chennai", "Active", 540000.0, "Standard"),
    ("ACC104", "Lakshmi Narayanan", "Savings", 6200.0, "Bengaluru", "Active", 215000.0, "Standard"),
    ("ACC105", "Mohammed Farooq", "Current", 8500.0, "Erode", "Suspicious", 98000.0, "High Risk"),
    ("ACC106", "Ananya Krishnan", "Salary", 5100.0, "Chennai", "Active", 142000.0, "Standard"),
    ("ACC107", "Vikram Rathore", "Business", 28000.0, "Mumbai", "Active", 890000.0, "Standard"),
    ("ACC108", "Sneha Sharma", "Savings", 4200.0, "Delhi", "Active", 175000.0, "Standard"),
    ("ACC109", "Suresh Babu", "Savings", 3100.0, "Coimbatore", "Active", 62000.0, "Standard"),
    ("ACC110", "Ganesh Moorthy", "Savings", 5500.0, "Erode", "Active", 110000.0, "Standard"),
    ("ACC111", "Divya Venkat", "Salary", 7200.0, "Bengaluru", "Active", 310000.0, "Standard"),
    ("ACC112", "Arun Prakash", "Current", 18500.0, "Mumbai", "Active", 450000.0, "Standard"),
]


def seed_database():
    """Initializes tables and seeds 50+ realistic records."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if already seeded
    cursor.execute("SELECT COUNT(*) FROM transactions")
    if cursor.fetchone()[0] >= 50:
        print("[FraudGuard Seed] Database already seeded with transactions. Skipping.")
        conn.close()
        return

    print("[FraudGuard Seed] Seeding database with realistic Indian banking records...")

    # 1. Seed Admin User
    admin_hash = hash_password("admin123")
    cursor.execute("""
        INSERT OR REPLACE INTO users (id, email, password_hash, full_name, role)
        VALUES (1, 'admin@fraudguard.ai', ?, 'Security Operations Admin', 'Chief Fraud Risk Officer')
    """, (admin_hash,))

    # 2. Seed Accounts
    for acc in SAMPLE_ACCOUNTS:
        cursor.execute("""
            INSERT OR REPLACE INTO accounts
            (account_id, holder_name, account_type, avg_amount, typical_location, status, balance, risk_tier)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, acc)

    # 3. Seed Mule Links (Mule Ring: ACC101 -> ACC102 -> ACC105 -> ACC101 circular routing)
    mule_data = [
        ("ACC101", "ACC102", 75000.0, 45, 1, "Rapid Layered Hop (Hop 1)"),
        ("ACC102", "ACC105", 73500.0, 32, 1, "Immediate Smurfing Transfer (Hop 2)"),
        ("ACC105", "ACC101", 72000.0, 20, 1, "Circular Flow Washback (Loop Closure)"),
        ("ACC105", "ACC109", 45000.0, 120, 0, "Fan-out Extraction Link"),
        ("ACC108", "ACC105", 50000.0, 90, 0, "Dormant Funnel Link"),
    ]
    for m in mule_data:
        cursor.execute("""
            INSERT INTO mule_links
            (source_account, target_account, amount, velocity_seconds, is_circular, detected_pattern)
            VALUES (?, ?, ?, ?, ?, ?)
        """, m)

    # 4. Generate 55+ Transactions across various risk profiles
    now = datetime.now()
    transactions_to_create = []

    # A) Pre-defined Critical Threat: Erode to Dubai Impossible Velocity
    transactions_to_create.append({
        "transaction_id": "TXN-CRIT-9901",
        "account_id": "ACC101",
        "amount": 85000.0,
        "avg_amount": 4500.0,
        "location": "Dubai",
        "prev_location": "Erode",
        "timestamp": (now - timedelta(minutes=14)).strftime("%Y-%m-%d %H:%M:%S"),
        "time": "03:15 AM",
        "device_id": "DEV-IPHONE-DUB-9X",
        "new_device": 1,
        "merchant": "Dubai Gold & Diamond Park",
        "channel": "International Wire",
        "geo_velocity_kmh": 2840.0,
        "transaction_frequency": 8,
        "time_anomaly": 1,
        "location_change": 1,
        "amount_ratio": 85000.0 / 4500.0,
    })

    # B) Pre-defined Critical Threat: Rapid Burst Multi-transfer
    transactions_to_create.append({
        "transaction_id": "TXN-CRIT-9902",
        "account_id": "ACC105",
        "amount": 92000.0,
        "avg_amount": 8500.0,
        "location": "Erode",
        "prev_location": "Erode",
        "timestamp": (now - timedelta(minutes=28)).strftime("%Y-%m-%d %H:%M:%S"),
        "time": "02:40 AM",
        "device_id": "DEV-LINUX-BURST-01",
        "new_device": 1,
        "merchant": "Offshore Crypto Gateway",
        "channel": "IMPS Express",
        "geo_velocity_kmh": 0.0,
        "transaction_frequency": 9,
        "time_anomaly": 1,
        "location_change": 0,
        "amount_ratio": 92000.0 / 8500.0,
    })

    # C) High Risk: Excessive Amount Surge
    transactions_to_create.append({
        "transaction_id": "TXN-HIGH-8801",
        "account_id": "ACC102",
        "amount": 48500.0,
        "avg_amount": 3800.0,
        "location": "Mumbai",
        "prev_location": "Coimbatore",
        "timestamp": (now - timedelta(hours=2, minutes=10)).strftime("%Y-%m-%d %H:%M:%S"),
        "time": "01:20 AM",
        "device_id": "DEV-PIXEL-7A",
        "new_device": 1,
        "merchant": "Croma Electronics Chennai",
        "channel": "NetBanking",
        "geo_velocity_kmh": 850.0,
        "transaction_frequency": 4,
        "time_anomaly": 1,
        "location_change": 1,
        "amount_ratio": 48500.0 / 3800.0,
    })

    # D) Medium Risk Transactions
    for i in range(1, 9):
        acc = SAMPLE_ACCOUNTS[i % len(SAMPLE_ACCOUNTS)]
        amt = acc[3] * random.uniform(2.6, 4.0)
        t_time = now - timedelta(hours=random.randint(3, 18), minutes=random.randint(10, 50))
        transactions_to_create.append({
            "transaction_id": f"TXN-MED-70{i:02d}",
            "account_id": acc[0],
            "amount": round(amt, 2),
            "avg_amount": acc[3],
            "location": random.choice(["Coimbatore", "Chennai", "Bengaluru", "Mumbai"]),
            "prev_location": acc[4],
            "timestamp": t_time.strftime("%Y-%m-%d %H:%M:%S"),
            "time": t_time.strftime("%I:%M %p"),
            "device_id": f"DEV-SAMSUNG-A{i}2",
            "new_device": 1 if i % 2 == 0 else 0,
            "merchant": random.choice(MERCHANTS)[0],
            "channel": random.choice(["UPI", "IMPS", "POS Card"]),
            "geo_velocity_kmh": random.uniform(150, 420),
            "transaction_frequency": random.randint(2, 4),
            "time_anomaly": 0,
            "location_change": 1,
            "amount_ratio": round(amt / acc[3], 2),
        })

    # E) Normal / Low Risk Transactions (45+ items)
    for i in range(1, 46):
        acc = random.choice(SAMPLE_ACCOUNTS)
        merchant, channel = random.choice(MERCHANTS[:10])
        amt = acc[3] * random.uniform(0.15, 1.4)
        t_time = now - timedelta(hours=random.randint(1, 72), minutes=random.randint(1, 59))
        transactions_to_create.append({
            "transaction_id": f"TXN-NORM-10{i:02d}",
            "account_id": acc[0],
            "amount": round(amt, 2),
            "avg_amount": acc[3],
            "location": acc[4],
            "prev_location": acc[4],
            "timestamp": t_time.strftime("%Y-%m-%d %H:%M:%S"),
            "time": t_time.strftime("%I:%M %p"),
            "device_id": f"DEV-PRIMARY-{acc[0]}",
            "new_device": 0,
            "merchant": merchant,
            "channel": channel,
            "geo_velocity_kmh": random.uniform(0, 45),
            "transaction_frequency": random.randint(1, 2),
            "time_anomaly": 0,
            "location_change": 0,
            "amount_ratio": round(amt / acc[3], 2),
        })

    # Run full Hybrid Evaluation on all transactions and insert
    for txn in transactions_to_create:
        eval_result = detector.evaluate_transaction(txn)

        # 1. Insert transaction
        cursor.execute("""
            INSERT OR REPLACE INTO transactions
            (transaction_id, account_id, amount, currency, location, timestamp, device_id, new_device, merchant, channel, status)
            VALUES (?, ?, ?, 'INR', ?, ?, ?, ?, ?, ?, 'Processed')
        """, (
            txn["transaction_id"],
            txn["account_id"],
            txn["amount"],
            txn["location"],
            txn["timestamp"],
            txn["device_id"],
            txn["new_device"],
            txn["merchant"],
            txn["channel"],
        ))

        # 2. Insert risk analysis
        cursor.execute("""
            INSERT OR REPLACE INTO risk_analysis
            (transaction_id, rule_score, ml_score, hybrid_score, risk_level, color_code, reasons_json, breakdowns_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            txn["transaction_id"],
            eval_result["rule_score"],
            eval_result["ml_score"],
            eval_result["hybrid_score"],
            eval_result["risk_level"],
            eval_result["color_code"],
            json.dumps(eval_result["xai_reasons"]),
            json.dumps(eval_result["rule_breakdowns"]),
        ))

        # 3. Create Alert if High or Critical
        if eval_result["risk_level"] in ("HIGH", "CRITICAL"):
            status = "Open"
            cursor.execute("""
                INSERT INTO alerts (transaction_id, account_id, risk_level, risk_score, status)
                VALUES (?, ?, ?, ?, ?)
            """, (
                txn["transaction_id"],
                txn["account_id"],
                eval_result["risk_level"],
                eval_result["hybrid_score"],
                status,
            ))

    conn.commit()
    conn.close()
    print(f"[FraudGuard Seed] Successfully populated database with {len(transactions_to_create)} Indian context transactions and analysis!")


if __name__ == "__main__":
    seed_database()
