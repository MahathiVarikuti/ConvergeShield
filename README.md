# ConvergeShield - AI-Assisted OT Security Monitoring

> **Intelligent threat detection with human-centered explanations for industrial control systems** 🛡️

**AI-Assisted IT-OT Security Monitoring System**

A hackathon project for Hitachi that provides real-time anomaly detection, attack classification, and explainable AI for industrial control systems (ICS/SCADA).

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-green)
![ML](https://img.shields.io/badge/ML-XGBoost%20%7C%20RF%20%7C%20IF-orange)

## 🎯 Key Features

### 1. **Human-Centered Explainability** ⭐ NEW
- Translates technical features into operator-friendly language
- "Pump 6 Flow Rate elevated abnormally" instead of "F_PU6: 0.85"
- Attack pattern detection (Coordinated attack, Pump manipulation, etc.)
- Clear, actionable insights for industrial operators

### 2. **OT-Safe Recommendations** ⭐ NEW  
- Decision support, NOT automation
- Safe verification steps (no auto-blocking)
- Severity-based action checklists
- Component-specific guidance (pumps, tanks, valves)
- Safety-first principles for critical infrastructure

### 3. **Single-Page Dashboard** ⭐ NEW
- Everything visible at once (no tab switching)
- Clean visual hierarchy: Alert → Explanation → Action
- One-click attack simulation for demos
- Professional SOC-like appearance
- Color-coded severity indicators

### 4. Hybrid Detection Engine
- **Isolation Forest** - Unsupervised anomaly detection
- **Random Forest** - Stable classification  
- **XGBoost** - High-performance attack detection
- **Weighted Ensemble** - Optimized combination (F1: 0.70)

### 5. Explainable AI (SHAP)
- Feature attribution for every prediction
- Top contributing factors
- Physics-aware explanations

### 6. Cyber-Physical Validation
- SCADA-specific physics rules
- Tank level bounds checking
- Pump flow consistency validation
- Pressure anomaly detection

## 📊 Performance Metrics

| Model | Accuracy | Precision | Recall | F1 Score |
|-------|----------|-----------|--------|----------|
| Isolation Forest | 92.68% | 0.11 | 0.48 | 0.18 |
| Random Forest | 98.94% | 1.00 | 0.38 | 0.55 |
| **XGBoost** | **99.30%** | **0.90** | **0.67** | **0.77** |
| **Ensemble** | **99.18%** | **0.90** | **0.74** | **0.70** |

**📈 3.5x improvement over reference paper's CSAD (F1: 0.70 vs 0.20)**

### Unique Contributions Beyond Paper

✅ **Human-readable explanations** - Paper has none  
✅ **OT-safe recommendations** - Paper doesn't address operator safety  
✅ **Real-time detection** - Paper only does batch processing  
✅ **Single-page dashboard** - Paper has no UI implementation  
✅ **Physics validation layer** - Additional safety net

## 🛠️ Tech Stack

**Backend:**
- Python 3.10+
- Flask 3.0
- scikit-learn
- XGBoost
- SHAP

**Frontend:**
- HTML5 / CSS3 / JavaScript
- Bootstrap 5
- Chart.js
- DataTables

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Train Models (if not already trained)
```bash
python train.py
```

### 3. Run Application
```bash
python app.py
```

### 4. Access Dashboard
- **Main Dashboard:** http://127.0.0.1:5000/ ⭐ NEW Single-Page View
- **Legacy Dashboard:** http://127.0.0.1:5000/dashboard/old
- **Analytics:** http://127.0.0.1:5000/analytics
- **Incidents:** http://127.0.0.1:5000/incidents

### 5. Demo Attack Simulation

Click any simulation button on the dashboard:
- **Tank Attack** - Sensor manipulation (medium severity)
- **Pump Attack** - Actuator control (high severity)
- **Critical Attack** - Command injection (critical severity)

Watch as the system:
1. Detects the anomaly
2. Explains WHY in plain language
3. Recommends SAFE actions

### 6. Test via CLI (optional)
```bash
python test_dashboard.py
```

## 📁 Project Structure

```
hackathon/
├── app/
│   ├── __init__.py
│   ├── routes.py                      # Flask API endpoints
│   ├── models/
│   │   ├── ensemble.py                # ML ensemble (IF+RF+XGBoost)
│   │   ├── data_processor.py          # BATADAL preprocessing
│   │   ├── physics_validator.py       # SCADA physics rules
│   │   ├── shap_explainer.py          # SHAP explanations
│   │   ├── ips_recommender.py         # IPS recommendations
│   │   ├── feature_translator.py      # ⭐ Human-readable translations
│   │   ├── safe_recommender.py        # ⭐ OT-safe action engine
│   │   └── attack_simulator.py        # Attack simulation
│   ├── static/
│   │   ├── css/style.css
│   │   └── js/
│   │       ├── dashboard.js
│   │       ├── analytics.js
│   │       └── incidents.js
│   └── templates/
│       ├── dashboard_clean.html       # ⭐ NEW Single-page dashboard
│       ├── dashboard.html             # Legacy dashboard
│       ├── analytics.html
│       └── incidents.html
├── trained_models/                    # Pre-trained ML models
├── data/                              # BATADAL datasets
├── files/                             # Reference papers
├── train.py                           # Model training script
├── app.py                             # Flask application
├── test_dashboard.py                  # ⭐ API testing script
├── TECHNICAL_REPORT.md                # Comprehensive documentation
├── IMPLEMENTATION_GUIDE.md            # ⭐ NEW Implementation details
└── README.md
```
├── files/                      # Datasets
├── trained_models/             # Saved ML models
├── train.py                    # Training script
├── app.py                      # Flask entry point
└── requirements.txt
```

## 🔬 Datasets

- **BATADAL** - Water distribution SCADA dataset
  - 43 features (tank levels, pump flows, pressures)
  - Attack labels for supervised learning
  
- **Windows 7/10** - Host telemetry data
  - 126 process/system features
  - Ground truth attack labels

## ⚡ Key Differentiators

1. **Hybrid Detection** - Not just anomaly detection, but classification too
2. **Explainable AI** - SHAP-based reasoning (addresses paper's gap)
3. **Cyber-Physical Validation** - Rare + highly impactful feature
4. **Recommendation System** - Moves from detection → action
5. **Live Monitoring** - Real SOC-like experience

## 📈 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | System status |
| `/api/stream` | GET | Live data stream |
| `/api/predict` | POST | Predict single sample |
| `/api/metrics` | GET | Model performance |
| `/api/explain` | POST | SHAP explanation |
| `/api/ips/stats` | GET | IPS statistics |

## 🏆 Benchmark Comparison

vs. Reference Paper (Scientific Reports, 2025):

| Metric | Paper (CSAD) | ConvergeShield |
|--------|--------------|----------------|
| F1 Score | 0.20 | **0.70** |
| AUC-ROC | N/A | **0.97** |

**3.5x improvement** over paper's ensemble approach!

## 👥 Team

Built for Hitachi Hackathon 2024

## 📄 License

MIT License
