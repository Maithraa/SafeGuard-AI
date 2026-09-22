# FraudGuard AI 🛡️
### Production-Ready Enterprise Financial Fraud Detection & XAI Engine

FraudGuard AI is a real-time full-stack web application built for financial institutions, core banking systems, and fintech payment rails (UPI, IMPS, NEFT). It blends an unsupervised **scikit-learn Isolation Forest machine learning model** with a **deterministic 5-factor rule-based scoring matrix** to calculate hybrid risk scores (0–100) and generate Explainable AI (XAI) root-cause diagnoses for every transaction.

---

## 🎨 Strict Visual & UI Design Rules

- **Zero Capsule / Pill Elements**: No pill buttons, no capsule badges, no rounded search bars, no fully rounded cards.
- **Border Radius**: Strictly locked between **4px to 8px** across every component.
- **Color Architecture**:
  - **Landing Hero**: Deep Navy (`#0b132b`) to Dark Purple (`#1c1135`) rich gradient.
  - **Info / Narrative Sections**: Light Warm Cream / Off-White (`#f8f9fa` / `#f3f4f6`) with dark typography.
  - **Analytical Sections**: Dark Navy (`#111827`) with Slate Blue panels (`#1f2937`) and 1px crisp borders (`#374151`).
  - **Risk Accents**: Low (`#10b981`), Medium (`#f59e0b`), High (`#f97316`), Critical (`#dc2626`).
  - **Left Border Side Indicators**: 4px solid vertical colored lines on cards and table rows.
- **Typography**: Clean hierarchy with Inter and monospace numbers for financial amounts.

---

## 🧠 Machine Learning & Hybrid Risk Engine

### 1. Isolation Forest ML Pipeline (`ml_model.py`)
Trained on 8 behavioral vectors with `StandardScaler`:
1. `amount`: Current transaction value (₹ INR)
2. `avg_amount`: Historical customer baseline mean
3. `amount_ratio`: `amount / avg_amount`
4. `transaction_frequency`: Burst count within a 10-minute trailing window
5. `new_device`: Binary indicator for unverified hardware signatures
6. `location_change`: Binary indicator for geofence transitions
7. `time_anomaly`: Binary indicator for execution between 12:00 AM and 05:00 AM
8. `geo_velocity_kmh`: Calculated transit velocity between consecutive transactions

### 2. Deterministic Rule Matrix (`fraud_detection.py`)
- Amount Anomaly (`> 5x baseline`): **+25 points**
- Impossible Velocity (`> 800 km/h` or offshore terminal): **+20 points**
- New Unrecognized Hardware: **+20 points**
- Nocturnal Window (`12:00 AM – 05:00 AM`): **+15 points**
- Rapid Fire Cadence (`> 5 txns in 10 mins`): **+20 points**

### 3. Hybrid Formula & Tiers
$$\text{Hybrid Score} = 0.6 \times \text{Rule Score} + 0.4 \times \text{ML Anomaly Score}$$

- **0 – 30**: **LOW RISK** (Green `#10b981`)
- **31 – 60**: **MEDIUM RISK** (Yellow `#f59e0b`)
- **61 – 80**: **HIGH RISK** (Orange `#f97316`)
- **81 – 100**: **CRITICAL THREAT** (Red `#dc2626`)

### 4. Explainable AI (XAI)
Every flagged transaction returns 3 to 5 human-readable diagnostic bullets describing exact multiples, velocities, and hardware anomalies.

---

## 📁 Modular File Tree

```
fraudguard-ai/
├── app.py                      # Flask REST API server and view routing
├── database.py                 # SQLite schema, queries, and connection pool
├── fraud_detection.py          # Hybrid Rule + ML Scoring Engine & Explainable AI (XAI)
├── ml_model.py                 # Isolation Forest ML pipeline, training & persistence
├── seed_data.py                # 50+ realistic Indian context records (INR, Erode, Dubai)
├── requirements.txt            # Python dependencies
├── README.md                   # System documentation
├── .gitignore                  # Git ignore file
├── model/
│   └── isolation_forest.pkl    # Serialized scikit-learn model + scaler
├── database/
│   └── fraudguard.db           # SQLite relational database
├── templates/
│   ├── base.html               # Base layout shell with top navbar
│   ├── index.html              # Landing page with interactive SVG pipeline
│   ├── login.html              # Split-screen login with demo credentials
│   ├── dashboard.html          # Operational dashboard with live simulation
│   ├── transactions.html       # Full transactions ledger with risk filters
│   ├── transaction_details.html# Deep XAI audit view with spending deviations
│   ├── accounts.html           # Monitored accounts portfolio & quarantine
│   ├── account_details.html    # Account profile & history
│   ├── analytics.html          # HTML5 Canvas Mule Network visualizer
│   ├── alerts.html             # Active alert triage & instant remediation
│   ├── upload.html             # Drag-and-drop CSV batch upload
│   └── settings.html           # Algorithmic weights calibration
└── static/
    ├── css/
    │   └── style.css           # Strict rectangular styling (4-8px radius)
    └── js/
        └── app.js              # Chart.js, Live simulation AJAX, Canvas graph
```

---

## ⚡ Quick Start & Run Instructions

### 1. Install Dependencies
```bash
py -3.13 -m pip install -r requirements.txt
```

### 2. Start Application Server
```bash
py -3.13 app.py
```
*Note: On first startup, the application automatically trains the Isolation Forest ML model and seeds 50+ realistic Indian transactions and mule rings into SQLite.*

### 3. Open in Browser
Navigate to **`http://127.0.0.1:5000`**

### 4. Demo Login Credentials
- **Email**: `admin@fraudguard.ai`
- **Password**: `admin123`

---

## 🌟 Hackathon Jury Demo Walkthrough

1. **Landing Hero**: Open `http://127.0.0.1:5000` to view the Deep Navy & Dark Purple hero and interactive SVG pipeline flow.
2. **Instant Sign-In**: Click **Login** and use pre-filled demo credentials `admin@fraudguard.ai` / `admin123`.
3. **Live Transaction Simulation**:
   - On `/dashboard`, click the prominent red button **`[ Simulate Live Transaction ]`**.
   - Watch the instant AJAX modal display the intercepted **₹85,000 Dubai threat**, the solid rectangular progress bar, and 4 Explainable AI reasons.
   - Close modal and notice all dashboard counters, Doughnut charts, and the suspicious table update **smoothly in real-time without page reload**.
4. **Mule Network Analysis**:
   - Click **Mule Network** in the top navigation (`/analytics`).
   - Observe the interactive HTML5 canvas displaying account nodes (`ACC101` ➔ `ACC102` ➔ `ACC105`) with red animated circular routing washback loops.
5. **Batch CSV Upload**:
   - Navigate to `/upload`, click **Download Pre-built Hackathon Test CSV**, and drag & drop it into the dropzone.
   - Inspect the instant audit evaluation table and click **Download Master Fraud Report** to export CSV audit logs.
"# SafeGuard-AI" 
