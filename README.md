# DataMind AI — Autonomous Business Intelligence Platform

An intelligent, autonomous Data Analytics and Business Intelligence platform inspired by Microsoft Power BI, built to work dynamically with **any arbitrary dataset** without hardcoding columns, schemas, or chart choices.

---

## 🌟 Key Capabilities

1. **Multi-Format Ingestion**: Upload CSV, Excel (`.xlsx`, `.xls`), JSON, and Parquet files with automatic normalization, column header sanitization, and columnar Parquet conversion.
2. **Dynamic Schema & Semantic Profiling**:
   - Automated detection of data types: Float, Integer, String, Datetime, Boolean.
   - Semantic role detection: Continuous Measures (aggregations), Dimensions (grouping/slicing), Temporal/Time attributes, and Unique Identifiers.
   - Cardinality ratios, completeness score, duplicate row counts, and statistical profiles.
3. **Automatic Power BI-Class Dashboards**:
   - KPI Summary Cards with dynamic aggregations (`SUM`, `AVG`, `COUNT`), trend indicators, and human-readable formatting ($ / K / M / B).
   - Comparison Bar charts, Chronological Trend Line/Area charts, Segment Donut distributions, and Bi-variate Scatter plots.
   - Standardized chart specifications rendered dynamically using Apache ECharts with responsive resizing and dark theme.
   - Interactive chart-type switcher (switch between Bar, Line, Area, and Data Table on the fly).
4. **Interactive Cross-Filtering**: Slice and filter across detected categorical dimensions in real time with automatic KPI and chart recomputation.
5. **Ask Your Data (AI Data Chat)**:
   - Natural language query interface with deterministic DuckDB analytical SQL execution.
   - Multi-provider LLM support (Groq, OpenAI, Gemini) + built-in offline semantic planner that works 100% reliably out-of-the-box even without external API keys.
   - Zero hallucination: calculations are computed directly on DuckDB; AI explains verified evidence and attaches live charts.
6. **Automated AI Insights Engine**:
   - Multi-variable Pearson correlation matrix with ranked significance.
   - Statistical outlier & anomaly detection (Z-Score > 3σ / IQR).
   - Pareto concentration (80/20 rule, top category dominance).
   - Chronological net growth / decline rate detection.
7. **Predictive Analytics & AutoML Studio**:
   - Dynamic task detection: Regression, Classification, Time-Series Forecasting, and Clustering (K-Means).
   - Evaluation metrics: $R^2$, MAE, RMSE for regression; Accuracy, F1, Precision for classification.
   - Feature Importance & Explainability (SHAP / Tree-based weights).
   - Interactive "What-If" prediction playground for real-time model inference.
8. **Live Analytical DuckDB SQL Console**: Run raw read-only SQL queries directly against datasets with tabular inspection.

---

## 🏗️ Technology Architecture

```
User Browser (Modern React 19 + TypeScript + Tailwind CSS + Apache ECharts)
                          │ (Port 3005)
                          ▼
            Vite Reverse Proxy (/api -> :8005)
                          │
                          ▼
         FastAPI Backend (Python 3.14 + Uvicorn)
     ┌────────────────────┼─────────────────────┐
     ▼                    ▼                     ▼
Ingestion & Profiler   DuckDB SQL Engine   AutoML & AI Agent
(Polars & PyArrow)   (In-Memory Parquet)  (Scikit-Learn & Groq/LLM)
```

---

## 🚀 Quick Start Guide

### 1. Backend Setup
```bash
cd backend
# Create virtual environment
python -m venv ..\.venv
# Activate virtual environment
..\.venv\Scripts\activate
# Install dependencies
pip install -r requirements.txt
# Start FastAPI backend on port 8005
python -m uvicorn main:app --host 127.0.0.1 --port 8005 --reload
```

### 2. Frontend Setup
```bash
cd frontend
# Install packages
npm install
# Start development server on port 3005
npm run dev -- --host 127.0.0.1 --port 3005
```

Open your browser at: **`http://127.0.0.1:3005`**

---

## 📊 Pre-Loaded Sample Domains

DataMind AI comes with 4 pre-configured domain datasets to test immediately:
1. **Global Sales & Profitability** (1,000 orders across 5 regions, 6 products, discount rates, revenue, and profit).
2. **Student Academic Performance** (800 students across 6 departments with attendance rates, study hours, midterm marks, and final grades).
3. **Hospital Patient Diagnostics** (600 patients with diagnoses, blood pressure, cholesterol, length of stay, and treatment costs).
4. **Corporate Financial Transactions** (1,200 transactions across categories, account types, amounts, and anomaly flags).
