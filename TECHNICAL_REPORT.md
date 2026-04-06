# ConvergeShield: AI-Assisted IT-OT Security Monitoring System

## Technical Report

**Hitachi Hackathon 2024**

---

## Table of Contents

1. [Problem Understanding](#1-problem-understanding)
2. [Literature Review](#2-literature-review)
3. [Proposed System](#3-proposed-system)
4. [Dataset Description](#4-dataset-description)
5. [Methodology](#5-methodology)
6. [Results](#6-results)
7. [Unique Contributions](#7-unique-contributions)
8. [Future Scope](#8-future-scope)

---

## 1. Problem Understanding

### 1.1 IT-OT Convergence Challenges

Traditional Operational Technology (OT) systems, including SCADA (Supervisory Control and Data Acquisition) and ICS (Industrial Control Systems), were designed as isolated networks with proprietary protocols. However, the convergence of IT and OT has introduced several security challenges:

- **Increased Attack Surface**: OT devices now connected to corporate networks and the internet
- **Legacy Vulnerabilities**: OT systems often run outdated software without security patches
- **Limited Telemetry**: OT devices provide minimal security-relevant information
- **Real-time Requirements**: Security solutions cannot introduce latency in critical processes

### 1.2 Why OT Security is Hard

| Challenge | Description |
|-----------|-------------|
| Resource Constraints | OT devices have limited CPU/memory for security agents |
| Protocol Diversity | Modbus, DNP3, IEC 61850 - non-standard protocols |
| Availability Priority | Systems cannot be taken offline for updates |
| Domain Gap | IT security tools don't understand physical processes |

### 1.3 Need for AI Monitoring

Traditional signature-based IDS fail in OT environments because:
- **Zero-day attacks** have no signatures
- **Insider threats** use legitimate credentials
- **Physical manipulation** doesn't trigger network alerts

AI-based anomaly detection can identify deviations from normal operational patterns, making it ideal for OT security.

---

## 2. Literature Review

### 2.1 Reference Paper Summary

**"Robust IoT Security using Isolation Forest and One Class SVM Algorithms"**
*Scientific Reports, 2025*

The paper proposes an anomaly detection framework using:
- **Isolation Forest (IF)**: Unsupervised tree-based anomaly detection
- **One-Class SVM (OCSVM)**: Boundary-based outlier detection
- **CSAD**: Combined Scoring Anomaly Detection (score fusion)

**Key Results on TON_IoT Dataset:**

| Model | Accuracy | Precision | Recall | F1 Score |
|-------|----------|-----------|--------|----------|
| OCSVM | 93.32% | 0.84 | 1.00 | 0.91 |
| IF | 63.02% | 0.37 | 0.08 | 0.13 |
| CSAD | 66.00% | 0.55 | 0.12 | 0.20 |

### 2.2 Limitations Identified

1. **Binary Classification Only**: Attack vs Normal - no attack type identification
2. **No Real-time Capability**: Batch processing only
3. **Limited Explainability**: Black-box predictions without reasoning
4. **No Physical Context**: Ignores domain-specific OT knowledge
5. **No Actionable Output**: Detection without recommendations

### 2.3 Our Improvements

> "ConvergeShield addresses all five limitations by providing multi-model ensemble classification, real-time monitoring, SHAP-based explainability, cyber-physical validation, and an IPS recommendation engine."

---

## 3. Proposed System

### 3.1 System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      ConvergeShield                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐                                               │
│  │ Data Sources │  BATADAL (SCADA) + Windows Telemetry          │
│  └──────┬───────┘                                               │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────┐                                               │
│  │ Preprocessing│  Scaling, Feature Selection, SMOTE            │
│  └──────┬───────┘                                               │
│         │                                                        │
│         ▼                                                        │
│  ┌─────────────────────────────────────────────────┐            │
│  │           Detection Engine (Layer 1 + 2)         │            │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐    │            │
│  │  │ Isolation │  │  Random   │  │  XGBoost  │    │            │
│  │  │  Forest   │  │  Forest   │  │ Classifier│    │            │
│  │  │ (Anomaly) │  │  (Class)  │  │  (Class)  │    │            │
│  │  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘    │            │
│  │        └──────────────┼──────────────┘          │            │
│  │                       ▼                          │            │
│  │            ┌─────────────────┐                   │            │
│  │            │ Weighted Ensemble│                   │            │
│  │            │   (25/40/35)    │                   │            │
│  │            └────────┬────────┘                   │            │
│  └─────────────────────┼───────────────────────────┘            │
│                        │                                         │
│         ┌──────────────┼──────────────┐                         │
│         ▼              ▼              ▼                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │   Physics   │ │    SHAP     │ │     IPS     │               │
│  │  Validator  │ │  Explainer  │ │ Recommender │               │
│  └─────────────┘ └─────────────┘ └─────────────┘               │
│         │              │              │                         │
│         └──────────────┼──────────────┘                         │
│                        ▼                                         │
│              ┌─────────────────┐                                │
│              │   Flask API     │                                │
│              └────────┬────────┘                                │
│                       ▼                                          │
│  ┌──────────────────────────────────────────────────┐           │
│  │                  Web Dashboard                    │           │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐       │           │
│  │  │Dashboard │  │Incidents │  │Analytics │       │           │
│  │  │  (Live)  │  │(Explorer)│  │ (Metrics)│       │           │
│  │  └──────────┘  └──────────┘  └──────────┘       │           │
│  └──────────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Pipeline Flow

1. **Data Ingestion**: Load SCADA telemetry (simulated real-time)
2. **Preprocessing**: StandardScaler normalization
3. **SMOTE Oversampling**: Balance training data (1.7% → 33% attacks)
4. **Model Training**: Train IF, RF, XGBoost in parallel
5. **Ensemble Voting**: Weighted combination (IF: 25%, RF: 40%, XGB: 35%)
6. **Physics Validation**: Apply cyber-physical rules
7. **SHAP Explanation**: Generate feature attributions
8. **IPS Recommendation**: Classify attack type, suggest actions
9. **Dashboard Display**: Real-time visualization

### 3.3 Model Explanation

| Model | Type | Purpose | Hyperparameters |
|-------|------|---------|-----------------|
| Isolation Forest | Unsupervised | Zero-day detection | n_estimators=150, contamination=0.15 |
| Random Forest | Supervised | Stable classification | n_estimators=150, max_depth=20, class_weight={0:1, 1:5} |
| XGBoost | Supervised | High performance | n_estimators=150, max_depth=10, scale_pos_weight=3 |

---

## 4. Dataset Description

### 4.1 BATADAL Dataset (Primary)

**Battle of the Attack Detection Algorithms** - Water distribution SCADA dataset

| Property | Value |
|----------|-------|
| Total Samples | 12,938 |
| Features | 43 |
| Normal Samples | 12,719 (98.3%) |
| Attack Samples | 219 (1.7%) |
| Time Period | Jan 2014 - Jul 2016 |

**Feature Categories:**

| Category | Features | Description |
|----------|----------|-------------|
| Tank Levels | L_T1 - L_T7 | Water levels in 7 tanks (meters) |
| Pump Flows | F_PU1 - F_PU11 | Flow rates (L/s) |
| Pump Status | S_PU1 - S_PU11 | ON/OFF status |
| Pressures | P_J* (12 features) | Junction pressures (psi) |
| Valve | F_V2, S_V2 | Valve flow and status |

**Attack Types in Dataset:**
- Sensor manipulation
- Actuator manipulation  
- Communication disruption
- Coordinated multi-stage attacks

### 4.2 Windows 7/10 Telemetry (Secondary)

| Property | Windows 10 | Windows 7 |
|----------|------------|-----------|
| Samples | 21,104 | Similar |
| Features | 126 | 126 |
| Ground Truth | Separate CSV | Separate CSV |

**Feature Categories:**
- Processor metrics (DPC rate, idle time, interrupts)
- Process metrics (IO operations, working set)
- Memory metrics (pool usage)
- Network metrics (if available)

---

## 5. Methodology

### 5.1 Data Preprocessing

```python
# 1. Load and combine datasets
df_train = pd.read_csv('BATADAL_dataset03.csv')  # Normal operations
df_test = pd.read_csv('BATADAL_dataset04.csv')   # With attacks

# 2. Handle missing/invalid values
df['ATT_FLAG'] = df['ATT_FLAG'].replace(-999, 0)

# 3. Feature-label separation
X = df[feature_columns].values
y = df['ATT_FLAG'].values

# 4. Train-test split (70-30, stratified)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, stratify=y, random_state=42
)

# 5. StandardScaler normalization
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)
```

### 5.2 SMOTE Oversampling

To address the severe class imbalance (1.7% attacks):

```python
from imblearn.over_sampling import SMOTE

smote = SMOTE(sampling_strategy=0.5, random_state=42)
X_resampled, y_resampled = smote.fit_resample(X_train_scaled, y_train)

# Before: 8903 normal, 153 attacks
# After:  8903 normal, 4451 attacks (33% minority)
```

### 5.3 Model Training

**Isolation Forest (Anomaly Detection):**
```python
IsolationForest(
    n_estimators=150,
    contamination=0.15,  # Expect 15% anomalies
    max_samples='auto',
    random_state=42
)
```

**Random Forest (Classification):**
```python
RandomForestClassifier(
    n_estimators=150,
    max_depth=20,
    class_weight={0: 1, 1: 5},  # 5x weight for attacks
    random_state=42
)
```

**XGBoost (Classification):**
```python
XGBClassifier(
    n_estimators=150,
    max_depth=10,
    scale_pos_weight=3,  # Class imbalance handling
    eval_metric='aucpr',
    random_state=42
)
```

### 5.4 Ensemble Logic

Weighted voting with optimized weights:

```python
weights = {
    'isolation_forest': 0.25,
    'random_forest': 0.40,
    'xgboost': 0.35
}

ensemble_score = (
    0.25 * if_score +
    0.40 * rf_proba +
    0.35 * xgb_proba
)

prediction = 1 if ensemble_score >= 0.35 else 0  # Lower threshold for recall
```

### 5.5 Cyber-Physical Validation Rules

```python
class PhysicsValidator:
    def check_pump_flow_consistency(self, sample):
        """If pump is OFF (S_PU=0), flow must be ~0"""
        for pump_id in range(1, 12):
            status = sample[f'S_PU{pump_id}']
            flow = sample[f'F_PU{pump_id}']
            if status == 0 and flow > 5:
                return {'violation': 'pump_flow_inconsistent', 'severity': 'critical'}
    
    def check_tank_bounds(self, sample):
        """Tank levels must be within physical limits"""
        for tank_id in range(1, 8):
            level = sample[f'L_T{tank_id}']
            if level < 0 or level > 10:
                return {'violation': 'tank_out_of_bounds', 'severity': 'high'}
    
    def check_rate_of_change(self, current, previous):
        """Detect impossible rate changes (data injection attack)"""
        max_rate = 2.0  # meters per time unit
        for tank_id in range(1, 8):
            rate = abs(current[f'L_T{tank_id}'] - previous[f'L_T{tank_id}'])
            if rate > max_rate:
                return {'violation': 'impossible_rate_change', 'severity': 'critical'}
```

---

## 6. Results

### 6.1 Model Performance Metrics

| Model | Accuracy | Precision | Recall | F1 Score | AUC-ROC |
|-------|----------|-----------|--------|----------|---------|
| Isolation Forest | 70.69% | 0.041 | 0.727 | 0.078 | - |
| Random Forest | 99.07% | 0.841 | 0.561 | 0.673 | - |
| **XGBoost** | **99.18%** | **0.783** | **0.712** | **0.746** | - |
| **Ensemble** | **98.87%** | **0.645** | **0.742** | **0.690** | **0.972** |

### 6.2 Confusion Matrix (Ensemble)

```
                    Predicted
                 Normal  Anomaly
Actual Normal    3789      27     (FP = 27)
Actual Anomaly     17      49     (FN = 17)

True Positives:  49 (correctly detected attacks)
True Negatives:  3789 (correctly identified normal)
False Positives: 27 (false alarms)
False Negatives: 17 (missed attacks)
```

### 6.3 Comparison with Reference Paper

| Model | Paper F1 | Our F1 | Improvement |
|-------|----------|--------|-------------|
| Isolation Forest | 0.13 | 0.08 | Different use case* |
| CSAD Ensemble | 0.20 | **0.69** | **+245%** |
| OCSVM | 0.91 | N/A | Different dataset |

*Note: Our IF focuses on high recall (0.73) for anomaly flagging, not classification

### 6.4 Feature Importance (Top 10)

| Rank | Feature | Importance | Description |
|------|---------|------------|-------------|
| 1 | P_J280 | 0.170 | Junction pressure |
| 2 | F_PU6 | 0.115 | Pump 6 flow rate |
| 3 | S_PU2 | 0.105 | Pump 2 status |
| 4 | F_PU11 | 0.050 | Pump 11 flow rate |
| 5 | F_PU10 | 0.042 | Pump 10 flow rate |
| 6 | P_J317 | 0.036 | Junction pressure |
| 7 | F_PU1 | 0.031 | Pump 1 flow rate |
| 8 | S_PU7 | 0.028 | Pump 7 status |
| 9 | F_PU7 | 0.026 | Pump 7 flow rate |
| 10 | P_J307 | 0.025 | Junction pressure |

### 6.5 Recall Improvement Analysis

After applying SMOTE and hyperparameter tuning:

| Model | Before | After | Improvement |
|-------|--------|-------|-------------|
| IF Recall | 0.48 | 0.73 | +52% |
| RF Recall | 0.38 | 0.56 | +47% |
| XGB Recall | 0.67 | 0.71 | +6% |
| Ensemble Recall | 0.58 | 0.74 | +28% |

---

## 7. Unique Contributions

### ⭐ 7.1 Hybrid Detection (Anomaly + Classification)

Unlike the reference paper's binary approach, ConvergeShield:
- Uses IF for unsupervised anomaly flagging (catches zero-days)
- Uses RF + XGBoost for attack type classification
- Combines both for robust detection

### ⭐ 7.2 SHAP-Based Explainability

Every prediction includes human-readable explanations:

```
This anomaly was flagged primarily due to:
  1. F_PU6: ↓ reduced (value=11.92, impact=-0.182)
  2. S_PU6: ↓ reduced (value=10.80, impact=-0.164)
  3. F_PU7: ↓ reduced (value=-2.28, impact=-0.083)
```

This addresses the paper's limitation of black-box predictions.

### ⭐ 7.3 Cyber-Physical Validation (VERY UNIQUE)

Our physics-based rule engine validates ML predictions against physical constraints:
- Pump OFF but flow detected → Critical violation
- Tank level out of bounds → Attack indicator
- Impossible rate of change → Data injection attack

This bridges the IT-OT gap that traditional tools miss.

### ⭐ 7.4 IPS Recommendation System

Moves from detection to action:

| Attack Type | Severity | Recommendation |
|-------------|----------|----------------|
| Pump Manipulation | Critical | Isolate pump controllers, verify PLC |
| Tank Overflow | Critical | Enable manual controls, alert operators |
| Pressure Attack | High | Cross-verify with physical gauges |
| Data Injection | High | Enable redundant sensor validation |

### ⭐ 7.5 Real-Time Monitoring Dashboard

Professional SOC-like interface with:
- Live packet stream visualization
- Real-time anomaly detection
- Interactive SHAP explanations
- SCADA component status display

---

## 8. Attack Simulation Lab

### 8.1 Attack Types Simulated

ConvergeShield includes a comprehensive attack simulation lab for demonstration and testing:

| Attack Type | MITRE ATT&CK ID | Description | Severity |
|-------------|-----------------|-------------|----------|
| Sensor Manipulation | T0832 | False data injection into tank/pressure sensors | Critical |
| Actuator Manipulation | T0855 | Unauthorized control of pumps/valves | Critical |
| Command Injection | T0821 | Malicious PLC commands | Critical |
| Man-in-the-Middle | T0830 | Intercepting/modifying SCADA traffic | Critical |
| DoS Flood | T0814 | Network flooding causing erratic readings | High |
| Replay Attack | T0843 | Replaying captured legitimate traffic | Medium |
| Reconnaissance | T0846 | Network scanning/probing | Low |

### 8.2 Network Traffic Simulation

Simulates Modbus TCP, DNP3, Siemens S7, OPC-UA, and MQTT protocols:
- Zeek-style connection logs (`conn.log`)
- Notice logs for detected threats
- Realistic packet metadata with threat scores

### 8.3 Multi-Stage Attack Sequences

Simulates realistic attack chains:
1. **Reconnaissance** (10%): Network discovery
2. **Initial Access** (20%): Probe sensors
3. **Escalation** (40%): Actuator manipulation
4. **Impact** (30%): Full attack execution

---

## 9. Future Scope

1. **Deep Learning Integration**: Add LSTM/Transformer for temporal patterns
2. **Edge Deployment**: Lightweight models for IoT gateways
3. **Real SCADA Integration**: Connect to actual Modbus/DNP3 protocols
4. **Adversarial Robustness**: Defense against evasion attacks
5. **Federated Learning**: Privacy-preserving training across sites
6. **Multi-site Correlation**: Detect coordinated attacks across facilities
7. **Real Tool Integration**: Connect with OpenPLC, Conpot, Zeek

---

## References

1. Zahoor, A., et al. "Robust IoT security using isolation forest and one class SVM algorithms." Scientific Reports 15, 36586 (2025).
2. BATADAL Dataset: https://www.batadal.net/
3. SHAP: Lundberg, S.M., Lee, S.I. "A Unified Approach to Interpreting Model Predictions." NeurIPS 2017.
4. MITRE ATT&CK for ICS: https://attack.mitre.org/techniques/ics/

---

## Appendix: API Documentation

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | System health check |
| `/api/stream` | GET | Get next sample from live stream |
| `/api/predict` | POST | Predict single sample |
| `/api/metrics` | GET | Get model performance metrics |
| `/api/explain` | POST | Get SHAP explanation |
| `/api/ips/stats` | GET | Get IPS statistics |
| `/api/ips/clear` | POST | Clear incident log |
| `/api/attack/types` | GET | Get available attack types |
| `/api/attack/simulate` | POST | Simulate specific attack |
| `/api/attack/sequence` | POST | Simulate multi-stage attack |
| `/api/traffic/generate` | GET | Generate network packets |

---

*Report generated for Hitachi Hackathon 2024*
*ConvergeShield: AI-Assisted IT-OT Security Monitoring System*
