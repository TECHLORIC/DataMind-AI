import os
import uuid
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, GradientBoostingRegressor, GradientBoostingClassifier
from sklearn.linear_model import Ridge, LogisticRegression, LinearRegression
from sklearn.tree import DecisionTreeRegressor, DecisionTreeClassifier
from sklearn.metrics import (
    r2_score, mean_absolute_error, mean_squared_error,
    accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
)
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from app.config import MODELS_DIR
from app.models.schemas import (
    DatasetProfile, MLTrainRequest, MLTrainResponse,
    MLPredictRequest, MLPredictResponse
)
from app.engine.dashboard_generator import format_number

class MLEngine:
    @staticmethod
    def train_model(parquet_path: Path, profile: DatasetProfile, request: MLTrainRequest) -> MLTrainResponse:
        """
        Dynamically trains baseline machine learning models with multi-algorithm comparison,
        rich visual diagnostics (Actual vs Predicted, Residuals, Confusion Matrix, Target Distribution),
        feature importance, and interactive What-If feature metadata.
        """
        parquet_path = Path(parquet_path)
        df = pd.read_parquet(parquet_path)

        task_type = request.task_type or "auto"
        target_col = request.target_column
        feature_cols = request.feature_columns

        # Auto-detect target column if not provided
        if not target_col and task_type != "clustering":
            if profile.primary_measures:
                target_col = profile.primary_measures[0]
            elif profile.primary_dimensions:
                target_col = profile.primary_dimensions[0]
            else:
                target_col = df.columns[-1]

        # Auto-detect task type
        if task_type == "auto":
            if target_col in df.columns:
                target_dtype = df[target_col].dtype
                unique_vals = df[target_col].nunique()

                if pd.api.types.is_numeric_dtype(target_dtype) and unique_vals > 10:
                    task_type = "regression"
                else:
                    task_type = "classification"
            else:
                task_type = "clustering"

        # Auto-select feature columns
        if not feature_cols:
            excluded = set()
            if target_col:
                excluded.add(target_col)
            if profile.primary_id_column:
                excluded.add(profile.primary_id_column)
            if profile.primary_time_column:
                excluded.add(profile.primary_time_column)

            feature_cols = [c for c in df.columns if c not in excluded]

        if not feature_cols and task_type != "forecasting":
            raise ValueError("No valid feature columns available for model training.")

        model_id = f"ml_{uuid.uuid4().hex[:10]}"
        metrics = {}
        feature_importance_list = []
        leaderboard = []
        target_distribution = None
        actual_vs_predicted = None
        residuals = None
        conf_matrix = None
        forecast_data = None
        cluster_centers = None
        algo_name = ""
        best_pipeline = None

        # Build feature metadata for What-If UI (min, max, step, sample values)
        feature_meta = {}
        for f in feature_cols:
            if f in df.columns:
                is_num = bool(pd.api.types.is_numeric_dtype(df[f]))
                if is_num:
                    f_min = float(df[f].min()) if not pd.isna(df[f].min()) else 0.0
                    f_max = float(df[f].max()) if not pd.isna(df[f].max()) else 100.0
                    f_mean = float(df[f].mean()) if not pd.isna(df[f].mean()) else 0.0
                    f_median = float(df[f].median()) if not pd.isna(df[f].median()) else 0.0
                    feature_meta[f] = {
                        "type": "numeric",
                        "min": round(f_min, 2),
                        "max": round(f_max, 2),
                        "mean": round(f_mean, 2),
                        "median": round(f_median, 2),
                        "default": round(f_median, 2)
                    }
                else:
                    unique_vals = [str(x) for x in df[f].dropna().unique()[:20]]
                    feature_meta[f] = {
                        "type": "categorical",
                        "categories": unique_vals,
                        "default": unique_vals[0] if unique_vals else ""
                    }

        # ---------------------------------------------------------
        # TASK 1: REGRESSION (Continuous Target)
        # ---------------------------------------------------------
        if task_type == "regression":
            clean_df = df.dropna(subset=[target_col]).copy()
            X = clean_df[feature_cols]
            y = clean_df[target_col].astype(float)

            # Compute Target Distribution (Histogram Bins)
            try:
                hist_vals, bin_edges = np.histogram(y.dropna(), bins=12)
                target_distribution = {
                    "type": "continuous",
                    "labels": [f"{bin_edges[i]:.1f} - {bin_edges[i+1]:.1f}" for i in range(len(hist_vals))],
                    "values": [int(v) for v in hist_vals]
                }
            except Exception:
                pass

            numeric_features = [c for c in feature_cols if pd.api.types.is_numeric_dtype(clean_df[c])]
            categorical_features = [c for c in feature_cols if c not in numeric_features]

            num_transformer = Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler())
            ])
            cat_transformer = Pipeline([
                ("imputer", SimpleImputer(strategy="constant", fill_value="missing")),
                ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
            ])

            preprocessor = ColumnTransformer(
                transformers=[
                    ("num", num_transformer, numeric_features),
                    ("cat", cat_transformer, categorical_features)
                ]
            )

            # Train 3 models for comparison
            models_to_test = [
                ("Random Forest", RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)),
                ("Gradient Boosting", GradientBoostingRegressor(n_estimators=100, max_depth=5, random_state=42)),
                ("Ridge Regression", Ridge(alpha=1.0))
            ]

            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

            best_r2 = -float("inf")
            for m_name, model_candidate in models_to_test:
                pipe = Pipeline([("preprocessor", preprocessor), ("regressor", model_candidate)])
                pipe.fit(X_train, y_train)
                preds = pipe.predict(X_test)
                cand_r2 = float(r2_score(y_test, preds))
                cand_mae = float(mean_absolute_error(y_test, preds))

                leaderboard.append({
                    "algorithm": m_name,
                    "primary_metric": "R² Score",
                    "score": round(max(0.0, cand_r2), 4),
                    "mae": round(cand_mae, 3),
                    "is_best": False
                })

                if cand_r2 > best_r2:
                    best_r2 = cand_r2
                    algo_name = m_name
                    best_pipeline = pipe

            # Mark best in leaderboard
            for item in leaderboard:
                if item["algorithm"] == algo_name:
                    item["is_best"] = True

            # Evaluate best model
            y_pred = best_pipeline.predict(X_test)
            r2 = round(float(r2_score(y_test, y_pred)), 4)
            mae = round(float(mean_absolute_error(y_test, y_pred)), 3)
            rmse = round(float(np.sqrt(mean_squared_error(y_test, y_pred))), 3)

            metrics = {
                "r2_score": max(0.0, r2),
                "mae": mae,
                "rmse": rmse,
                "train_samples": len(X_train),
                "test_samples": len(X_test)
            }

            # Generate Actual vs Predicted Scatter Sample (up to 40 points)
            sample_size = min(40, len(y_test))
            sample_indices = np.random.RandomState(42).choice(len(y_test), sample_size, replace=False)
            test_arr = np.array(y_test)
            actual_vs_predicted = [
                {
                    "actual": round(float(test_arr[i]), 2),
                    "predicted": round(float(y_pred[i]), 2)
                }
                for i in sample_indices
            ]

            # Residuals (Error Distribution)
            error_arr = y_pred - test_arr
            residuals = [
                {"sample": idx + 1, "error": round(float(err), 2)}
                for idx, err in enumerate(error_arr[sample_indices])
            ]

            # Feature Importance
            try:
                regressor = best_pipeline.named_steps["regressor"]
                if hasattr(regressor, "feature_importances_"):
                    raw_imp = regressor.feature_importances_
                    cat_ohe = preprocessor.named_transformers_["cat"].named_steps["onehot"]
                    cat_names = cat_ohe.get_feature_names_out(categorical_features).tolist() if categorical_features else []
                    all_feat = numeric_features + cat_names
                    fi = sorted(zip(all_feat, raw_imp), key=lambda x: x[1], reverse=True)[:10]
                    total_imp = sum(x[1] for x in fi) or 1.0
                    feature_importance_list = [
                        {"feature": f[0], "importance": round(float(f[1]), 4), "percentage": round(float(f[1] / total_imp * 100), 1)}
                        for f in fi
                    ]
            except Exception:
                pass

            summary = f"Evaluated 3 algorithms. Top model '{algo_name}' achieved R² = {r2:.3f} and MAE = {format_number(mae)}."

        # ---------------------------------------------------------
        # TASK 2: CLASSIFICATION (Categorical / Discrete Target)
        # ---------------------------------------------------------
        elif task_type == "classification":
            clean_df = df.dropna(subset=[target_col]).copy()
            X = clean_df[feature_cols]
            y = clean_df[target_col].astype(str)

            # Class Distribution
            class_counts = y.value_counts().head(10).to_dict()
            target_distribution = {
                "type": "categorical",
                "labels": list(class_counts.keys()),
                "values": list(class_counts.values())
            }

            numeric_features = [c for c in feature_cols if pd.api.types.is_numeric_dtype(clean_df[c])]
            categorical_features = [c for c in feature_cols if c not in numeric_features]

            num_transformer = Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler())
            ])
            cat_transformer = Pipeline([
                ("imputer", SimpleImputer(strategy="constant", fill_value="missing")),
                ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
            ])

            preprocessor = ColumnTransformer(
                transformers=[
                    ("num", num_transformer, numeric_features),
                    ("cat", cat_transformer, categorical_features)
                ]
            )

            models_to_test = [
                ("Random Forest", RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)),
                ("Gradient Boosting", GradientBoostingClassifier(n_estimators=80, max_depth=4, random_state=42)),
                ("Logistic Regression", LogisticRegression(max_iter=500, random_state=42))
            ]

            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42,
                stratify=y if y.value_counts().min() > 1 else None
            )

            best_acc = -1.0
            for m_name, model_candidate in models_to_test:
                pipe = Pipeline([("preprocessor", preprocessor), ("classifier", model_candidate)])
                pipe.fit(X_train, y_train)
                preds = pipe.predict(X_test)
                cand_acc = float(accuracy_score(y_test, preds))

                leaderboard.append({
                    "algorithm": m_name,
                    "primary_metric": "Accuracy",
                    "score": round(cand_acc, 4),
                    "is_best": False
                })

                if cand_acc > best_acc:
                    best_acc = cand_acc
                    algo_name = m_name
                    best_pipeline = pipe

            for item in leaderboard:
                if item["algorithm"] == algo_name:
                    item["is_best"] = True

            y_pred = best_pipeline.predict(X_test)
            acc = round(float(accuracy_score(y_test, y_pred)), 4)
            f1 = round(float(f1_score(y_test, y_pred, average="weighted", zero_division=0)), 4)
            prec = round(float(precision_score(y_test, y_pred, average="weighted", zero_division=0)), 4)
            rec = round(float(recall_score(y_test, y_pred, average="weighted", zero_division=0)), 4)

            # Confusion Matrix
            labels = sorted(list(set(y_test)))[:8]
            cm = confusion_matrix(y_test, y_pred, labels=labels)
            conf_matrix = {
                "classes": labels,
                "matrix": cm.tolist()
            }

            metrics = {
                "accuracy": acc,
                "f1_score": f1,
                "precision": prec,
                "recall": rec,
                "classes": labels,
                "train_samples": len(X_train),
                "test_samples": len(X_test)
            }

            try:
                clf = best_pipeline.named_steps["classifier"]
                if hasattr(clf, "feature_importances_"):
                    raw_imp = clf.feature_importances_
                    cat_ohe = preprocessor.named_transformers_["cat"].named_steps["onehot"]
                    cat_names = cat_ohe.get_feature_names_out(categorical_features).tolist() if categorical_features else []
                    all_feat = numeric_features + cat_names
                    fi = sorted(zip(all_feat, raw_imp), key=lambda x: x[1], reverse=True)[:10]
                    total_imp = sum(x[1] for x in fi) or 1.0
                    feature_importance_list = [
                        {"feature": f[0], "importance": round(float(f[1]), 4), "percentage": round(float(f[1] / total_imp * 100), 1)}
                        for f in fi
                    ]
            except Exception:
                pass

            summary = f"Evaluated 3 classification models. Best algorithm '{algo_name}' reached {acc * 100:.1f}% Accuracy and F1 = {f1:.3f}."

        # ---------------------------------------------------------
        # TASK 3: TIME-SERIES FORECASTING
        # ---------------------------------------------------------
        elif task_type == "forecasting":
            time_col = request.time_column or profile.primary_time_column
            if not time_col or not target_col:
                raise ValueError("Forecasting requires a valid time column and a continuous target metric.")

            clean_df = df.dropna(subset=[time_col, target_col]).copy()
            clean_df[time_col] = pd.to_datetime(clean_df[time_col])
            ts = clean_df.sort_values(time_col).groupby(pd.Grouper(key=time_col, freq="ME"))[target_col].sum().reset_index()

            horizon = request.forecast_horizon or 12
            algo_name = "Autoregressive Linear Trend Forecaster"

            ts["step"] = np.arange(len(ts))
            step_reg = Ridge(alpha=1.0)
            step_reg.fit(ts[["step"]], ts[target_col])

            last_date = ts[time_col].max()
            future_steps = np.arange(len(ts), len(ts) + horizon).reshape(-1, 1)
            future_preds = step_reg.predict(future_steps)

            forecast_data = []
            # Include recent historical points for continuity
            for _, r in ts.tail(12).iterrows():
                forecast_data.append({
                    "period": r[time_col].strftime("%Y-%m"),
                    "actual": round(float(r[target_col]), 2),
                    "forecast": None,
                    "lower_bound": None,
                    "upper_bound": None
                })

            for i, p_val in enumerate(future_preds):
                f_date = (last_date + pd.DateOffset(months=i + 1)).strftime("%Y-%m")
                forecast_data.append({
                    "period": f_date,
                    "actual": None,
                    "forecast": round(float(max(0, p_val)), 2),
                    "lower_bound": round(float(max(0, p_val * 0.85)), 2),
                    "upper_bound": round(float(p_val * 1.15), 2)
                })

            hist_preds = step_reg.predict(ts[["step"]])
            r2 = round(float(r2_score(ts[target_col], hist_preds)), 4)
            metrics = {
                "r2_trend_fit": max(0.0, r2),
                "forecast_horizon_periods": horizon,
                "historical_periods": len(ts)
            }
            summary = f"Generated {horizon}-period forward forecast for '{target_col}' over time attribute '{time_col}'."
            best_pipeline = step_reg

        # ---------------------------------------------------------
        # TASK 4: CLUSTERING (K-Means)
        # ---------------------------------------------------------
        else:
            task_type = "clustering"
            algo_name = "K-Means Clustering"
            num_cols = [c for c in feature_cols if pd.api.types.is_numeric_dtype(df[c])]
            if not num_cols:
                raise ValueError("Clustering requires at least one numeric feature column.")

            X = df[num_cols].dropna()
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            k = 3 if len(X) > 30 else 2
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(X_scaled)

            counts = pd.Series(labels).value_counts().to_dict()
            metrics = {
                "num_clusters": k,
                "inertia": round(float(kmeans.inertia_), 2),
                "cluster_distribution": {f"Cluster {c}": count for c, count in counts.items()}
            }

            cluster_centers = []
            for idx, center in enumerate(scaler.inverse_transform(kmeans.cluster_centers_)):
                center_dict = {"cluster": f"Cluster {idx}"}
                for c_name, c_val in zip(num_cols, center):
                    center_dict[c_name] = round(float(c_val), 2)
                cluster_centers.append(center_dict)

            summary = f"Clustered {len(X):,} records into {k} behavioral segments using {algo_name}."
            best_pipeline = Pipeline([("scaler", scaler), ("kmeans", kmeans)])

        # Save model bundle
        model_save_path = MODELS_DIR / f"{model_id}.joblib"
        joblib.dump({
            "pipeline": best_pipeline,
            "task_type": task_type,
            "target_column": target_col,
            "feature_columns": feature_cols,
            "feature_meta": feature_meta,
            "algorithm_name": algo_name,
            "metrics": metrics
        }, model_save_path)

        return MLTrainResponse(
            model_id=model_id,
            dataset_id=profile.dataset_id,
            task_type=task_type,
            target_column=target_col,
            features_used=feature_cols,
            algorithm_name=algo_name,
            metrics=metrics,
            feature_importance=feature_importance_list,
            model_leaderboard=leaderboard,
            target_distribution=target_distribution,
            actual_vs_predicted=actual_vs_predicted,
            residuals=residuals,
            confusion_matrix=conf_matrix,
            forecast_data=forecast_data,
            cluster_centers=cluster_centers,
            feature_meta=feature_meta,
            created_at=datetime.datetime.utcnow().isoformat(),
            summary=summary
        )

    @staticmethod
    def predict(model_id: str, request: MLPredictRequest) -> MLPredictResponse:
        """Loads saved model and evaluates inference against input features with robust type coercion."""
        model_file = MODELS_DIR / f"{model_id}.joblib"
        if not model_file.exists():
            raise FileNotFoundError(f"Model {model_id} not found.")

        bundle = joblib.load(model_file)
        pipeline = bundle["pipeline"]
        task_type = bundle["task_type"]
        feature_cols = bundle["feature_columns"]
        target_col = bundle["target_column"]
        feature_meta = bundle.get("feature_meta", {})

        # Handle forecasting or clustering
        if task_type == "forecasting":
            step_val = float(request.features.get("step", 1))
            pred_raw = pipeline.predict(np.array([[step_val]]))[0]
            formatted_pred = round(float(max(0, pred_raw)), 2)
            return MLPredictResponse(
                model_id=model_id,
                prediction=formatted_pred,
                explanation=f"Forecasted {target_col}: {formatted_pred}"
            )

        # Build clean row with coerced types matching training pipeline
        row = {}
        for col in feature_cols:
            raw_val = request.features.get(col, None)
            meta = feature_meta.get(col, {})
            is_num = meta.get("type") == "numeric"

            if is_num:
                try:
                    if raw_val is None or raw_val == "":
                        row[col] = [meta.get("median", 0.0)]
                    else:
                        row[col] = [float(raw_val)]
                except (ValueError, TypeError):
                    row[col] = [meta.get("median", 0.0)]
            else:
                row[col] = [str(raw_val) if raw_val is not None else "missing"]

        input_df = pd.DataFrame(row)

        pred_val = pipeline.predict(input_df)[0]
        probabilities = None
        confidence = None

        if task_type == "classification" and hasattr(pipeline, "predict_proba"):
            try:
                probs = pipeline.predict_proba(input_df)[0]
                classes = pipeline.classes_
                probabilities = {str(c): round(float(p), 4) for c, p in zip(classes, probs)}
                confidence = round(float(max(probs)), 4)
            except Exception:
                pass

        if isinstance(pred_val, (np.integer, int)):
            formatted_pred = int(pred_val)
        elif isinstance(pred_val, (np.floating, float)):
            formatted_pred = round(float(pred_val), 3)
        else:
            formatted_pred = str(pred_val)

        explanation = f"Model predicts {target_col or 'output'} = {formatted_pred}"
        if confidence:
            explanation += f" with {confidence * 100:.1f}% confidence."

        return MLPredictResponse(
            model_id=model_id,
            prediction=formatted_pred,
            probabilities=probabilities,
            confidence=confidence,
            explanation=explanation
        )
