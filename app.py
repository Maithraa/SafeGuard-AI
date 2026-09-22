"""
FraudGuard AI - Web Application & REST API Server
Flask application serving all dynamic views and REST API endpoints for fraud detection.
"""

import os
import json
import csv
import io
import random
from datetime import datetime, timedelta
from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    session,
    Response,
)

from database import (
    init_db,
    get_db_connection,
    save_transaction_and_analysis,
    get_dashboard_metrics,
)
from fraud_detection import detector
from seed_data import seed_database, hash_password

app = Flask(__name__)
app.secret_key = "fraudguard-ai-secret-key-production-hackathon-2026"

# Ensure DB and seed data exist on startup
with app.app_context():
    init_db()
    seed_database()


# ---------------------------------------------------------------------------
# Frontend Page Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/transactions")
def transactions_page():
    return render_template("transactions.html")


@app.route("/transactions/<txn_id>")
def transaction_details_page(txn_id):
    return render_template("transaction_details.html", txn_id=txn_id)


@app.route("/accounts")
def accounts_page():
    return render_template("accounts.html")


@app.route("/accounts/<account_id>")
def account_details_page(account_id):
    return render_template("account_details.html", account_id=account_id)


@app.route("/analytics")
def analytics_page():
    return render_template("analytics.html")


@app.route("/alerts")
def alerts_page():
    return render_template("alerts.html")


@app.route("/upload")
def upload_page():
    return render_template("upload.html")


@app.route("/settings")
def settings_page():
    return render_template("settings.html")


# ---------------------------------------------------------------------------
# Authentication API
# ---------------------------------------------------------------------------

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json() or {}
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()

    if not email or not password:
        return jsonify({"success": False, "message": "Email and password required"}), 400

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()

    if user and user["password_hash"] == hash_password(password):
        session["user_id"] = user["id"]
        session["user_email"] = user["email"]
        session["user_name"] = user["full_name"]
        return jsonify({
            "success": True,
            "redirect": "/dashboard",
            "user": {
                "email": user["email"],
                "name": user["full_name"],
                "role": user["role"],
            }
        })
    elif email == "admin@fraudguard.ai" and password == "admin123":
        # Fallback admin credential
        session["user_id"] = 1
        session["user_email"] = email
        session["user_name"] = "Security Operations Admin"
        return jsonify({
            "success": True,
            "redirect": "/dashboard",
            "user": {
                "email": email,
                "name": "Security Operations Admin",
                "role": "Chief Fraud Risk Officer",
            }
        })

    return jsonify({"success": False, "message": "Invalid email or password"}), 401


# ---------------------------------------------------------------------------
# Dashboard Analytics API
# ---------------------------------------------------------------------------

@app.route("/api/dashboard", methods=["GET"])
def api_dashboard():
    metrics = get_dashboard_metrics()
    conn = get_db_connection()

    # Get recent 10 suspicious/critical transactions with account details
    suspicious_rows = conn.execute("""
        SELECT t.transaction_id, t.account_id, t.amount, t.currency, t.location,
               t.timestamp, t.channel, t.merchant, a.holder_name,
               r.hybrid_score, r.risk_level, r.color_code, r.reasons_json
        FROM transactions t
        JOIN risk_analysis r ON t.transaction_id = r.transaction_id
        JOIN accounts a ON t.account_id = a.account_id
        WHERE r.risk_level IN ('HIGH', 'CRITICAL')
        ORDER BY t.timestamp DESC
        LIMIT 10
    """).fetchall()

    recent_suspicious = []
    for row in suspicious_rows:
        reasons = json.loads(row["reasons_json"]) if row["reasons_json"] else []
        recent_suspicious.append({
            "transaction_id": row["transaction_id"],
            "account_id": row["account_id"],
            "holder_name": row["holder_name"],
            "amount": row["amount"],
            "currency": row["currency"],
            "location": row["location"],
            "timestamp": row["timestamp"],
            "channel": row["channel"],
            "merchant": row["merchant"],
            "hybrid_score": row["hybrid_score"],
            "risk_level": row["risk_level"],
            "color_code": row["color_code"],
            "xai_summary": reasons[0] if reasons else "Elevated risk profile detected",
        })

    # Hourly volume comparison (Simulated normal vs suspicious curve over 24h)
    hours = [f"{h:02d}:00" for h in range(24)]
    normal_hourly = [320, 180, 110, 95, 140, 260, 480, 750, 1100, 1450, 1620, 1580,
                     1490, 1550, 1720, 1880, 1940, 1820, 1690, 1520, 1380, 1120, 780, 510]
    suspicious_hourly = [18, 25, 42, 55, 38, 14, 8, 12, 16, 21, 24, 19,
                         22, 28, 31, 35, 30, 26, 22, 29, 34, 40, 36, 27]

    conn.close()

    return jsonify({
        "metrics": metrics,
        "recent_suspicious": recent_suspicious,
        "hourly_trend": {
            "hours": hours,
            "normal": normal_hourly,
            "suspicious": suspicious_hourly,
        }
    })


# ---------------------------------------------------------------------------
# Transactions API
# ---------------------------------------------------------------------------

@app.route("/api/transactions", methods=["GET"])
def api_transactions():
    search = request.args.get("search", "").strip()
    risk_filter = request.args.get("risk", "").strip().upper()
    limit = int(request.args.get("limit", 100))

    conn = get_db_connection()
    query = """
        SELECT t.transaction_id, t.account_id, t.amount, t.currency, t.location,
               t.timestamp, t.device_id, t.channel, t.merchant, t.status,
               a.holder_name, a.typical_location,
               r.rule_score, r.ml_score, r.hybrid_score, r.risk_level, r.color_code, r.reasons_json
        FROM transactions t
        JOIN accounts a ON t.account_id = a.account_id
        JOIN risk_analysis r ON t.transaction_id = r.transaction_id
        WHERE 1=1
    """
    params = []

    if search:
        query += " AND (t.transaction_id LIKE ? OR t.account_id LIKE ? OR a.holder_name LIKE ? OR t.location LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term, term])

    if risk_filter and risk_filter in ("LOW", "MEDIUM", "HIGH", "CRITICAL"):
        query += " AND r.risk_level = ?"
        params.append(risk_filter)

    query += " ORDER BY t.timestamp DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    conn.close()

    results = []
    for r in rows:
        reasons = json.loads(r["reasons_json"]) if r["reasons_json"] else []
        results.append({
            "transaction_id": r["transaction_id"],
            "account_id": r["account_id"],
            "holder_name": r["holder_name"],
            "amount": r["amount"],
            "currency": r["currency"],
            "location": r["location"],
            "typical_location": r["typical_location"],
            "timestamp": r["timestamp"],
            "channel": r["channel"],
            "merchant": r["merchant"],
            "status": r["status"],
            "rule_score": r["rule_score"],
            "ml_score": r["ml_score"],
            "hybrid_score": r["hybrid_score"],
            "risk_level": r["risk_level"],
            "color_code": r["color_code"],
            "xai_reasons": reasons,
        })

    return jsonify({"transactions": results, "count": len(results)})


@app.route("/api/transactions/<txn_id>", methods=["GET"])
def api_transaction_details(txn_id):
    conn = get_db_connection()
    row = conn.execute("""
        SELECT t.*, a.holder_name, a.avg_amount, a.typical_location, a.balance, a.account_type, a.status as account_status,
               r.rule_score, r.ml_score, r.hybrid_score, r.risk_level, r.color_code,
               r.reasons_json, r.breakdowns_json
        FROM transactions t
        JOIN accounts a ON t.account_id = a.account_id
        JOIN risk_analysis r ON t.transaction_id = r.transaction_id
        WHERE t.transaction_id = ?
    """, (txn_id,)).fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Transaction not found"}), 404

    reasons = json.loads(row["reasons_json"]) if row["reasons_json"] else []
    breakdowns = json.loads(row["breakdowns_json"]) if row["breakdowns_json"] else []

    return jsonify({
        "transaction": {
            "transaction_id": row["transaction_id"],
            "account_id": row["account_id"],
            "holder_name": row["holder_name"],
            "amount": row["amount"],
            "currency": row["currency"],
            "location": row["location"],
            "typical_location": row["typical_location"],
            "timestamp": row["timestamp"],
            "device_id": row["device_id"],
            "new_device": bool(row["new_device"]),
            "merchant": row["merchant"],
            "channel": row["channel"],
            "status": row["status"],
            "account_balance": row["balance"],
            "account_type": row["account_type"],
            "avg_amount": row["avg_amount"],
            "account_status": row["account_status"],
        },
        "analysis": {
            "rule_score": row["rule_score"],
            "ml_score": row["ml_score"],
            "hybrid_score": row["hybrid_score"],
            "risk_level": row["risk_level"],
            "color_code": row["color_code"],
            "reasons": reasons,
            "breakdowns": breakdowns,
        }
    })


# ---------------------------------------------------------------------------
# Real-Time Simulation API Flow (CRITICAL FOR HACKATHON JURY)
# ---------------------------------------------------------------------------

@app.route("/api/simulate-transaction", methods=["POST"])
def api_simulate_transaction():
    """
    Generates a realistic simulated high-risk transaction:
    - Amount: ₹85,000 (typical avg: ₹4,500)
    - Location: Dubai (previous location: Erode)
    - Time: 03:15 AM
    - New Device: Yes (DEV-ROGUE-EMIRATES-09)
    - Velocity: 2,850 km/h
    - 8 transactions in 10 mins
    Runs Rule Engine + Isolation Forest ML inference, commits to DB, and returns XAI reasons.
    """
    now = datetime.now()
    sim_id = f"TXN-SIM-{random.randint(10000, 99999)}"

    sim_txn = {
        "transaction_id": sim_id,
        "account_id": "ACC101",
        "amount": 85000.0,
        "avg_amount": 4500.0,
        "location": "Dubai",
        "prev_location": "Erode",
        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
        "time": "03:15 AM",
        "device_id": "DEV-ROGUE-EMIRATES-09",
        "new_device": 1,
        "merchant": "Al-Maktoum Gold & Jewelry Dubai",
        "channel": "IMPS International",
        "geo_velocity_kmh": 2850.0,
        "transaction_frequency": 8,
        "time_anomaly": 1,
        "location_change": 1,
        "amount_ratio": 85000.0 / 4500.0,
        "currency": "INR",
        "status": "Flagged / Under Review",
    }

    # Execute Hybrid Fraud Engine
    analysis = detector.evaluate_transaction(sim_txn)

    # Persist to database
    alert_id = save_transaction_and_analysis(sim_txn, analysis)

    return jsonify({
        "success": True,
        "message": "Live high-risk transaction successfully intercepted and analyzed.",
        "transaction": sim_txn,
        "analysis": analysis,
        "alert_id": alert_id,
        "refreshed_metrics": get_dashboard_metrics(),
    })


# ---------------------------------------------------------------------------
# CSV Batch Upload API
# ---------------------------------------------------------------------------

@app.route("/api/upload", methods=["POST"])
def api_upload():
    """
    Parses CSV with columns:
    transaction_id, account_id, amount, avg_amount, location, time, new_device, transactions_10min
    Processes rules + ML, saves to DB, returns processing summary.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
    reader = csv.DictReader(stream)

    results = []
    high_critical_count = 0

    now = datetime.now()
    row_count = 0

    for row in reader:
        row_count += 1
        txn_id = row.get("transaction_id", f"TXN-CSV-{row_count:04d}").strip()
        acc_id = row.get("account_id", "ACC101").strip()
        amount = float(row.get("amount", 1000.0))
        avg_amount = float(row.get("avg_amount", 1000.0))
        location = row.get("location", "Erode").strip()
        time_str = row.get("time", "14:30").strip()
        new_device = int(row.get("new_device", 0))
        frequency = int(row.get("transactions_10min", 1))

        # Infer velocity & time anomaly
        is_foreign = location.lower() in ["dubai", "london", "singapore", "new york", "seychelles"]
        velocity = 2400.0 if is_foreign else (450.0 if location != "Erode" else 15.0)

        hour = 14
        try:
            hour = int(time_str.split(":")[0])
        except Exception:
            pass
        time_anomaly = 1 if 0 <= hour <= 5 else 0

        txn_payload = {
            "transaction_id": txn_id,
            "account_id": acc_id,
            "amount": amount,
            "avg_amount": avg_amount,
            "location": location,
            "prev_location": "Erode",
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "time": time_str,
            "device_id": f"DEV-CSV-{acc_id}",
            "new_device": new_device,
            "merchant": "Batch Upload Merchant",
            "channel": "UPI",
            "geo_velocity_kmh": velocity,
            "transaction_frequency": frequency,
            "time_anomaly": time_anomaly,
            "location_change": 1 if location != "Erode" else 0,
            "amount_ratio": amount / max(avg_amount, 1.0),
            "currency": "INR",
            "status": "Processed",
        }

        # Run detection
        analysis = detector.evaluate_transaction(txn_payload)
        save_transaction_and_analysis(txn_payload, analysis)

        if analysis["risk_level"] in ("HIGH", "CRITICAL"):
            high_critical_count += 1

        results.append({
            "transaction_id": txn_id,
            "account_id": acc_id,
            "amount": amount,
            "location": location,
            "hybrid_score": analysis["hybrid_score"],
            "risk_level": analysis["risk_level"],
            "color_code": analysis["color_code"],
            "top_reason": analysis["xai_reasons"][0] if analysis["xai_reasons"] else "Standard clearance",
        })

    return jsonify({
        "success": True,
        "rows_processed": row_count,
        "high_critical_flagged": high_critical_count,
        "records": results[:20],  # Return first 20 for preview
    })


@app.route("/api/download-report")
def api_download_report():
    """Generates a downloadable CSV fraud audit report."""
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT t.transaction_id, t.account_id, a.holder_name, t.amount, t.currency,
               t.location, t.timestamp, t.channel,
               r.rule_score, r.ml_score, r.hybrid_score, r.risk_level, r.reasons_json
        FROM transactions t
        JOIN accounts a ON t.account_id = a.account_id
        JOIN risk_analysis r ON t.transaction_id = r.transaction_id
        ORDER BY r.hybrid_score DESC
    """).fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Transaction ID", "Account ID", "Account Holder", "Amount (INR)",
        "Location", "Timestamp", "Channel", "Rule Score", "ML Score",
        "Hybrid Score", "Risk Level", "Primary XAI Reason"
    ])

    for row in rows:
        reasons = json.loads(row["reasons_json"]) if row["reasons_json"] else []
        primary_reason = reasons[0] if reasons else "None"
        writer.writerow([
            row["transaction_id"],
            row["account_id"],
            row["holder_name"],
            row["amount"],
            row["location"],
            row["timestamp"],
            row["channel"],
            row["rule_score"],
            row["ml_score"],
            row["hybrid_score"],
            row["risk_level"],
            primary_reason
        ])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=FraudGuard_Audit_Report.csv"}
    )


# ---------------------------------------------------------------------------
# Accounts & Mule Network API
# ---------------------------------------------------------------------------

@app.route("/api/accounts", methods=["GET"])
def api_accounts():
    conn = get_db_connection()
    accounts = conn.execute("""
        SELECT a.*,
               COUNT(t.transaction_id) as txn_count,
               MAX(r.hybrid_score) as max_risk_score
        FROM accounts a
        LEFT JOIN transactions t ON a.account_id = t.account_id
        LEFT JOIN risk_analysis r ON t.transaction_id = r.transaction_id
        GROUP BY a.account_id
        ORDER BY max_risk_score DESC
    """).fetchall()
    conn.close()

    results = []
    for a in accounts:
        results.append({
            "account_id": a["account_id"],
            "holder_name": a["holder_name"],
            "account_type": a["account_type"],
            "avg_amount": a["avg_amount"],
            "typical_location": a["typical_location"],
            "status": a["status"],
            "balance": a["balance"],
            "risk_tier": a["risk_tier"],
            "txn_count": a["txn_count"],
            "max_risk_score": a["max_risk_score"] or 15.0,
        })
    return jsonify({"accounts": results})


@app.route("/api/accounts/<account_id>", methods=["GET"])
def api_account_details(account_id):
    conn = get_db_connection()
    account = conn.execute("SELECT * FROM accounts WHERE account_id = ?", (account_id,)).fetchone()
    if not account:
        conn.close()
        return jsonify({"error": "Account not found"}), 404

    # Related transactions
    txns = conn.execute("""
        SELECT t.*, r.hybrid_score, r.risk_level, r.color_code, r.reasons_json
        FROM transactions t
        JOIN risk_analysis r ON t.transaction_id = r.transaction_id
        WHERE t.account_id = ?
        ORDER BY t.timestamp DESC
    """, (account_id,)).fetchall()

    # Mule connections
    mule_links = conn.execute("""
        SELECT * FROM mule_links
        WHERE source_account = ? OR target_account = ?
    """, (account_id, account_id)).fetchall()

    conn.close()

    txn_list = []
    for t in txns:
        reasons = json.loads(t["reasons_json"]) if t["reasons_json"] else []
        txn_list.append({
            "transaction_id": t["transaction_id"],
            "amount": t["amount"],
            "currency": t["currency"],
            "location": t["location"],
            "timestamp": t["timestamp"],
            "channel": t["channel"],
            "merchant": t["merchant"],
            "hybrid_score": t["hybrid_score"],
            "risk_level": t["risk_level"],
            "color_code": t["color_code"],
            "xai_reason": reasons[0] if reasons else "Clear",
        })

    mules = []
    for m in mule_links:
        mules.append({
            "source": m["source_account"],
            "target": m["target_account"],
            "amount": m["amount"],
            "velocity_seconds": m["velocity_seconds"],
            "is_circular": bool(m["is_circular"]),
            "pattern": m["detected_pattern"],
        })

    return jsonify({
        "account": dict(account),
        "transactions": txn_list,
        "mule_links": mules,
    })


# ---------------------------------------------------------------------------
# Analytics & Mule Graph API
# ---------------------------------------------------------------------------

@app.route("/api/analytics", methods=["GET"])
def api_analytics():
    conn = get_db_connection()
    links = conn.execute("SELECT * FROM mule_links").fetchall()

    # Build node and link structure for canvas graph
    nodes_dict = {}
    edges = []

    for l in links:
        src = l["source_account"]
        tgt = l["target_account"]
        amt = l["amount"]
        is_circ = bool(l["is_circular"])

        if src not in nodes_dict:
            nodes_dict[src] = {"id": src, "label": src, "risk": "CRITICAL" if is_circ else "MEDIUM"}
        if tgt not in nodes_dict:
            nodes_dict[tgt] = {"id": tgt, "label": tgt, "risk": "CRITICAL" if is_circ else "MEDIUM"}

        edges.append({
            "source": src,
            "target": tgt,
            "amount": amt,
            "is_circular": is_circ,
            "velocity": l["velocity_seconds"],
            "label": f"₹{amt:,.0f} ({l['velocity_seconds']}s)",
        })

    # Location threat volume
    loc_stats = conn.execute("""
        SELECT t.location, COUNT(*) as txn_count,
               AVG(r.hybrid_score) as avg_risk,
               SUM(CASE WHEN r.risk_level IN ('HIGH', 'CRITICAL') THEN 1 ELSE 0 END) as flagged_count
        FROM transactions t
        JOIN risk_analysis r ON t.transaction_id = r.transaction_id
        GROUP BY t.location
        ORDER BY flagged_count DESC
    """).fetchall()

    threat_geo = []
    for ls in loc_stats:
        threat_geo.append({
            "location": ls["location"],
            "count": ls["txn_count"],
            "avg_risk": round(ls["avg_risk"], 1),
            "flagged": ls["flagged_count"],
        })

    conn.close()

    return jsonify({
        "mule_graph": {
            "nodes": list(nodes_dict.values()),
            "edges": edges,
        },
        "geo_threats": threat_geo,
    })


# ---------------------------------------------------------------------------
# Alerts Triage & Disposition API
# ---------------------------------------------------------------------------

@app.route("/api/alerts", methods=["GET"])
def api_alerts():
    conn = get_db_connection()
    alerts = conn.execute("""
        SELECT al.alert_id, al.transaction_id, al.account_id, al.risk_level, al.risk_score,
               al.status, al.resolution_action, al.created_at,
               t.amount, t.currency, t.location, t.timestamp, t.channel,
               a.holder_name,
               r.reasons_json
        FROM alerts al
        JOIN transactions t ON al.transaction_id = t.transaction_id
        JOIN accounts a ON al.account_id = a.account_id
        JOIN risk_analysis r ON al.transaction_id = r.transaction_id
        ORDER BY al.created_at DESC
    """).fetchall()
    conn.close()

    result = []
    for a in alerts:
        reasons = json.loads(a["reasons_json"]) if a["reasons_json"] else []
        result.append({
            "alert_id": a["alert_id"],
            "transaction_id": a["transaction_id"],
            "account_id": a["account_id"],
            "holder_name": a["holder_name"],
            "amount": a["amount"],
            "currency": a["currency"],
            "location": a["location"],
            "timestamp": a["timestamp"],
            "channel": a["channel"],
            "risk_level": a["risk_level"],
            "risk_score": a["risk_score"],
            "status": a["status"],
            "resolution_action": a["resolution_action"],
            "created_at": a["created_at"],
            "primary_reason": reasons[0] if reasons else "Elevated risk index",
        })

    return jsonify({"alerts": result, "total": len(result)})


@app.route("/api/alerts/<int:alert_id>/action", methods=["POST"])
def api_alert_action(alert_id):
    """
    Executes triage action on alert:
    - Freeze (freezes account and locks funds)
    - Limit (imposes strict ₹2,000 transaction ceiling)
    - Review (moves alert to active SOC tier-2 review)
    - Dismiss (marks alert as false positive)
    """
    data = request.get_json() or {}
    action = data.get("action", "").capitalize()

    if action not in ["Freeze", "Limit", "Review", "Dismiss"]:
        return jsonify({"error": "Invalid action. Must be Freeze, Limit, Review, or Dismiss."}), 400

    conn = get_db_connection()
    alert = conn.execute("SELECT * FROM alerts WHERE alert_id = ?", (alert_id,)).fetchone()
    if not alert:
        conn.close()
        return jsonify({"error": "Alert not found"}), 404

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Update alert record
    conn.execute("""
        UPDATE alerts
        SET status = ?, resolution_action = ?, resolved_at = ?
        WHERE alert_id = ?
    """, (f"Resolved ({action})", action, now_str, alert_id))

    # If action is Freeze or Limit, update account status
    if action == "Freeze":
        conn.execute("UPDATE accounts SET status = 'Frozen' WHERE account_id = ?", (alert["account_id"],))
    elif action == "Limit":
        conn.execute("UPDATE accounts SET status = 'Restricted' WHERE account_id = ?", (alert["account_id"],))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "alert_id": alert_id,
        "action": action,
        "message": f"Action '{action}' applied successfully to Account {alert['account_id']}."
    })


if __name__ == "__main__":
    print("=" * 60)
    print("  FraudGuard AI Server Starting on http://127.0.0.1:5000")
    print("  Default Auth: admin@fraudguard.ai / admin123")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=True)
