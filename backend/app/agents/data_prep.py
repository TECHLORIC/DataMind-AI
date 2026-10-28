import datetime
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
from scipy import stats
from app.models.domain.dataset import (
    ColumnMeta,
    DatasetProfile,
    DataCleaningReport,
    KPISpec,
    DashboardSpec,
    ChartSpec
)
from app.utils.formatting import format_number, format_percentage

class DataPrepAgent:
    """
    Automated Data Preparation & Profiling Agent.
    Cleans data, performs intelligent missing value imputation,
    deduplicates, computes statistical health metrics, and generates
    dashboard-ready specifications.
    """

    @staticmethod
    def _try_parse_datetime_series(series: pd.Series, col_name: str) -> Tuple[bool, pd.Series]:
        """
        Robustly parses a series into datetime64 across multiple formats:
        ISO, DD/MM/YYYY, MM/DD/YYYY, DD-MM-YYYY, DD.MM.YYYY, text months, Excel serials, etc.
        """
        # 1. Already datetime64
        if pd.api.types.is_datetime64_any_dtype(series):
            return True, series

        # 2. Check hints from column name
        name_hints = [
            "date", "time", "timestamp", "year", "month", "day", "created", "updated", 
            "period", "quarter", "shipped", "delivered", "received", "dob", "expiry", 
            "closed", "resolved", "submitted", "logged", "start", "end"
        ]
        has_name_hint = any(k in col_name.lower() for k in name_hints)

        # 3. Check sample values for date-like string patterns
        non_null_samples = series.dropna().astype(str).head(50)
        if len(non_null_samples) == 0:
            return False, series

        date_pattern = re.compile(
            r"(\d{4}[-/.]\d{1,2}[-/.]\d{1,2})"       # 2024-01-15, 2024/01/15, 2024.01.15
            r"|(\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4})"    # 15/01/2024, 01/15/2024, 15-01-2024
            r"|(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{2,4})"  # 15 Jan 2024, 15 January 2024
            r"|([A-Za-z]{3,9}\s+\d{1,2},?\s+\d{2,4})" # Jan 15, 2024, January 15 2024
        )
        pattern_matches = sum(bool(date_pattern.search(str(val))) for val in non_null_samples)
        has_content_hint = (pattern_matches / len(non_null_samples)) >= 0.5

        if pd.api.types.is_numeric_dtype(series) and not has_name_hint:
            return False, series

        if not (has_name_hint or has_content_hint):
            return False, series

        # Numeric date heuristics (Excel serials or 4-digit Year)
        if pd.api.types.is_numeric_dtype(series):
            valid_nums = series.dropna()
            # 4-digit years
            if len(valid_nums) > 0 and valid_nums.min() >= 1900 and valid_nums.max() <= 2100 and "year" in col_name.lower():
                try:
                    dt = pd.to_datetime(series.astype(str) + "-01-01", errors="coerce")
                    if dt.notnull().sum() / len(valid_nums) >= 0.8:
                        return True, dt
                except Exception:
                    pass

            # Excel serial days (30000 to 65000 is ~1982 to ~2078)
            if len(valid_nums) > 0 and 30000 <= valid_nums.min() and valid_nums.max() <= 65000 and has_name_hint:
                try:
                    dt = pd.to_datetime(series, unit="D", origin="1899-12-30", errors="coerce")
                    if dt.notnull().sum() / len(valid_nums) >= 0.7:
                        return True, dt
                except Exception:
                    pass

        # Strategy 1: format='mixed' (robust across disparate formats in one column)
        try:
            dt = pd.to_datetime(series, format="mixed", errors="coerce")
            if dt.notnull().sum() / max(len(series), 1) >= 0.5:
                return True, dt
        except Exception:
            pass

        # Strategy 2: dayfirst=True with format='mixed'
        try:
            dt = pd.to_datetime(series, dayfirst=True, format="mixed", errors="coerce")
            if dt.notnull().sum() / max(len(series), 1) >= 0.5:
                return True, dt
        except Exception:
            pass

        # Strategy 3: Standard ISO parsing
        try:
            dt = pd.to_datetime(series, errors="coerce")
            if dt.notnull().sum() / max(len(series), 1) >= 0.5:
                return True, dt
        except Exception:
            pass

        # Strategy 4: Explicit format trial for stubborn formats
        explicit_formats = [
            "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%m-%d-%Y",
            "%Y/%m/%d", "%d.%m.%Y", "%Y.%m.%d", "%d %b %Y", "%d-%b-%Y",
            "%B %d, %Y", "%b %d, %Y", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S"
        ]
        for fmt in explicit_formats:
            try:
                dt = pd.to_datetime(series, format=fmt, errors="coerce")
                if dt.notnull().sum() / max(len(series), 1) >= 0.5:
                    return True, dt
            except Exception:
                continue

        return False, series

    @staticmethod
    def clean_and_profile(
        df: pd.DataFrame,
        dataset_id: str,
        name: str,
        filename: str,
        file_format: str,
        file_size_mb: float
    ) -> Tuple[pd.DataFrame, DatasetProfile, DashboardSpec]:
        original_rows = len(df)
        cleaning_actions: List[str] = []
        imputed_columns: List[str] = []
        total_missing_imputed = 0

        # 1. Drop completely empty columns and rows
        initial_cols = len(df.columns)
        df = df.dropna(how="all", axis=1)
        if len(df.columns) < initial_cols:
            diff = initial_cols - len(df.columns)
            cleaning_actions.append(f"Dropped {diff} completely empty column(s).")

        df = df.dropna(how="all", axis=0)
        if len(df) < original_rows:
            diff = original_rows - len(df)
            cleaning_actions.append(f"Dropped {diff} completely empty row(s).")

        # 2. Deduplication
        duplicates_count = int(df.duplicated().sum())
        if duplicates_count > 0:
            df = df.drop_duplicates()
            cleaning_actions.append(f"Removed {duplicates_count:,} duplicate row(s).")

        # 3. Type inference and Intelligent Missing Value Imputation
        columns_meta: List[ColumnMeta] = []
        primary_measures: List[str] = []
        primary_dimensions: List[str] = []
        primary_time_col: str = None
        primary_id_col: str = None

        total_cells = len(df) * len(df.columns)
        initial_null_cells = int(df.isnull().sum().sum())

        for col in df.columns:
            series = df[col]
            null_count = int(series.isnull().sum())
            total_missing_imputed += null_count
            unique_count = int(series.nunique())
            cardinality_ratio = float(unique_count / len(df)) if len(df) > 0 else 0.0

            # Determine type
            inferred_type = "string"
            semantic_type = "dimension"
            is_datetime = False
            is_numeric = False

            # 1. Check if datetime first (handles existing datetime64, varied date string formats, excel serials)
            is_dt, parsed_dt = DataPrepAgent._try_parse_datetime_series(series, col)
            if is_dt:
                df[col] = parsed_dt
                series = parsed_dt
                is_datetime = True
                inferred_type = "datetime"
                semantic_type = "time"
                if not primary_time_col:
                    primary_time_col = col
                cleaning_actions.append(f"Standardized diverse date formats in '{col}' to uniform timestamps.")

            # 2. Check if numeric
            if not is_datetime:
                is_numeric = pd.api.types.is_numeric_dtype(series)
                if not is_numeric:
                    converted = pd.to_numeric(series.astype(str).str.replace(r"[$,]", "", regex=True), errors="coerce")
                    if converted.notnull().sum() / max(len(series), 1) > 0.75:
                        df[col] = converted
                        series = converted
                        is_numeric = True

            # 3. Classify semantic type & statistics based on inferred type
            if is_datetime:
                pass  # already configured above

            elif is_numeric:
                inferred_type = "float" if pd.api.types.is_float_dtype(series) else "int"
                if any(k in col.lower() for k in ["id", "code", "zip", "ssn", "phone"]):
                    semantic_type = "identifier"
                    if not primary_id_col:
                        primary_id_col = col
                elif cardinality_ratio > 0.005 or unique_count > 10:
                    semantic_type = "measure"
                    primary_measures.append(col)
                else:
                    semantic_type = "dimension"
                    primary_dimensions.append(col)

                # Missing value imputation for numeric
                if null_count > 0:
                    valid_series = series.dropna()
                    skewness = float(stats.skew(valid_series)) if len(valid_series) > 3 else 0.0
                    if abs(skewness) > 1.0:
                        median_val = float(valid_series.median())
                        df[col] = series.fillna(median_val)
                        cleaning_actions.append(f"Imputed {null_count} null(s) in '{col}' using median ({median_val:.2f}).")
                    else:
                        mean_val = float(valid_series.mean())
                        df[col] = series.fillna(mean_val)
                        cleaning_actions.append(f"Imputed {null_count} null(s) in '{col}' using mean ({mean_val:.2f}).")
                    imputed_columns.append(col)

            else:
                inferred_type = "string"
                if cardinality_ratio > 0.9 and any(k in col.lower() for k in ["id", "uuid", "guid", "key"]):
                    semantic_type = "identifier"
                    if not primary_id_col:
                        primary_id_col = col
                else:
                    semantic_type = "dimension"
                    primary_dimensions.append(col)

                # Categorical missing imputation
                if null_count > 0:
                    mode_val = series.mode()[0] if not series.mode().empty else "Unknown"
                    if series.value_counts(normalize=True).iloc[0] > 0.5:
                        df[col] = series.fillna(mode_val)
                        cleaning_actions.append(f"Imputed {null_count} null(s) in '{col}' using mode ('{mode_val}').")
                    else:
                        df[col] = series.fillna("Unknown")
                        cleaning_actions.append(f"Filled {null_count} null(s) in '{col}' with 'Unknown'.")
                    imputed_columns.append(col)

            # Statistical Summary for ColumnMeta
            sample_vals = [str(x) for x in df[col].dropna().head(5).tolist()]
            min_v, max_v, mean_v, median_v, std_v = None, None, None, None, None
            if is_numeric:
                min_v = float(df[col].min())
                max_v = float(df[col].max())
                mean_v = float(df[col].mean())
                median_v = float(df[col].median())
                std_v = float(df[col].std())
            elif is_datetime:
                valid_dt = df[col].dropna()
                if not valid_dt.empty:
                    min_v = str(valid_dt.min())[:10]
                    max_v = str(valid_dt.max())[:10]

            columns_meta.append(ColumnMeta(
                name=col,
                data_type=inferred_type,
                semantic_type=semantic_type,
                nullable=null_count > 0,
                null_count=null_count,
                null_percentage=round((null_count / max(original_rows, 1)) * 100, 2),
                unique_count=unique_count,
                cardinality_ratio=round(cardinality_ratio, 4),
                sample_values=sample_vals,
                min_val=min_v,
                max_val=max_v,
                mean_val=mean_v,
                median_val=median_v,
                std_val=std_v
            ))

        # 4. Calculate Data Health Score (0 - 100%)
        null_penalty = min(40.0, (initial_null_cells / max(total_cells, 1)) * 100 * 2)
        duplicate_penalty = min(30.0, (duplicates_count / max(original_rows, 1)) * 100 * 3)
        health_score = max(10.0, round(100.0 - null_penalty - duplicate_penalty, 1))

        cleaning_report = DataCleaningReport(
            original_rows=original_rows,
            cleaned_rows=len(df),
            duplicates_removed=duplicates_count,
            missing_cells_imputed=total_missing_imputed,
            columns_imputed=imputed_columns,
            data_health_score=health_score,
            cleaning_actions=cleaning_actions
        )

        completeness = round(((total_cells - initial_null_cells) / max(total_cells, 1)) * 100, 2)
        memory_mb = round(float(df.memory_usage(deep=True).sum()) / (1024 * 1024), 3)

        profile = DatasetProfile(
            dataset_id=dataset_id,
            name=name,
            filename=filename,
            file_format=file_format,
            total_rows=len(df),
            total_columns=len(df.columns),
            completeness=completeness,
            duplicate_rows=duplicates_count,
            memory_usage_mb=memory_mb,
            columns=columns_meta,
            primary_measures=primary_measures[:5],
            primary_dimensions=primary_dimensions[:5],
            primary_time_column=primary_time_col,
            primary_id_column=primary_id_col,
            cleaning_report=cleaning_report,
            created_at=datetime.datetime.utcnow().isoformat()
        )

        # 5. Generate Initial Dashboard Specification
        dashboard = DataPrepAgent._build_dashboard_overview(df, profile)

        return df, profile, dashboard

    @staticmethod
    def _build_dashboard_overview(df: pd.DataFrame, profile: DatasetProfile) -> DashboardSpec:
        kpis: List[KPISpec] = []
        charts: List[ChartSpec] = []

        # KPI 1: Total Records
        kpis.append(KPISpec(
            id="kpi_total_records",
            title="Total Records",
            value=profile.total_rows,
            formatted_value=f"{profile.total_rows:,}",
            aggregation="count",
            measure_column="rows",
            trend_direction="neutral"
        ))

        # KPI 2: Data Health Score
        kpis.append(KPISpec(
            id="kpi_health_score",
            title="Data Health Score",
            value=profile.cleaning_report.data_health_score,
            formatted_value=f"{profile.cleaning_report.data_health_score}%",
            aggregation="score",
            measure_column="health",
            trend_direction="up" if profile.cleaning_report.data_health_score >= 80 else "neutral"
        ))

        # Measure KPIs
        for m in profile.primary_measures[:2]:
            s = df[m].dropna()
            val = float(s.sum()) if not s.empty else 0.0
            kpis.append(KPISpec(
                id=f"kpi_{m}",
                title=f"Total {m.replace('_', ' ').title()}",
                value=round(val, 2),
                formatted_value=format_number(val),
                aggregation="sum",
                measure_column=m,
                trend_direction="up" if val > 0 else "neutral"
            ))

        # Primary Comparison Chart
        if profile.primary_dimensions and profile.primary_measures:
            dim = profile.primary_dimensions[0]
            meas = profile.primary_measures[0]
            grouped = df.groupby(dim, as_index=False)[meas].sum().sort_values(by=meas, ascending=False).head(10)
            data = [{"category": str(r[dim]), "value": round(float(r[meas]), 2)} for _, r in grouped.iterrows()]
            
            charts.append(ChartSpec(
                id=f"chart_bar_{dim}_{meas}",
                chart_type="bar",
                title=f"{meas.replace('_', ' ').title()} by {dim.replace('_', ' ').title()}",
                description=f"Comparison of {meas} aggregated across top {dim} segments.",
                x_axis=dim,
                y_axis=meas,
                aggregation="sum",
                data=data,
                insight=f"Top segment '{data[0]['category']}' represents {format_number(data[0]['value'])}." if data else "",
                plotly_spec={
                    "data": [{
                        "type": "bar",
                        "x": [d["category"] for d in data],
                        "y": [d["value"] for d in data],
                        "marker": {"color": "#8b5cf6"}
                    }],
                    "layout": {
                        "title": f"{meas.replace('_', ' ').title()} by {dim.replace('_', ' ').title()}",
                        "template": "plotly_dark",
                        "paper_bgcolor": "rgba(0,0,0,0)",
                        "plot_bgcolor": "rgba(0,0,0,0)"
                    }
                }
            ))

        # Temporal Trend Chart
        if profile.primary_time_column and profile.primary_measures:
            time_c = profile.primary_time_column
            meas_c = profile.primary_measures[0]
            try:
                time_series = df.dropna(subset=[time_c, meas_c]).copy()
                if not pd.api.types.is_datetime64_any_dtype(time_series[time_c]):
                    time_series[time_c] = pd.to_datetime(time_series[time_c], format="mixed", errors="coerce")
                
                time_series["period"] = time_series[time_c].dt.strftime("%Y-%m")
                trend_df = time_series.groupby("period")[meas_c].sum().reset_index().sort_values("period").head(24)
                if len(trend_df) <= 1:
                    time_series["period"] = time_series[time_c].dt.strftime("%Y-%m-%d")
                    trend_df = time_series.groupby("period")[meas_c].sum().reset_index().sort_values("period").head(30)
                
                if len(trend_df) > 1:
                    trend_data = [{"category": str(r["period"]), "value": round(float(r[meas_c]), 2)} for _, r in trend_df.iterrows()]
                    charts.append(ChartSpec(
                        id=f"chart_trend_{time_c}_{meas_c}",
                        chart_type="line",
                        title=f"{meas_c.replace('_', ' ').title()} Over Time",
                        description=f"Monthly trajectory of {meas_c} across historical periods.",
                        x_axis=time_c,
                        y_axis=meas_c,
                        data=trend_data,
                        insight=f"Trend spans {trend_data[0]['category']} to {trend_data[-1]['category']} across {len(trend_data)} periods.",
                        plotly_spec={
                            "data": [{
                                "type": "scatter",
                                "mode": "lines+markers",
                                "x": [d["category"] for d in trend_data],
                                "y": [d["value"] for d in trend_data],
                                "line": {"color": "#38bdf8", "width": 3, "shape": "spline"},
                                "marker": {"size": 6, "color": "#0284c7"}
                            }],
                            "layout": {
                                "title": f"{meas_c.replace('_', ' ').title()} Monthly Trend",
                                "template": "plotly_dark",
                                "paper_bgcolor": "rgba(0,0,0,0)",
                                "plot_bgcolor": "rgba(0,0,0,0)"
                            }
                        }
                    ))
            except Exception:
                pass

        # Distribution Chart
        if len(profile.primary_dimensions) > 1:
            dim2 = profile.primary_dimensions[1]
            counts = df[dim2].value_counts().head(6)
            data2 = [{"category": str(idx), "value": int(cnt)} for idx, cnt in counts.items()]
            charts.append(ChartSpec(
                id=f"chart_donut_{dim2}",
                chart_type="donut",
                title=f"{dim2.replace('_', ' ').title()} Share",
                description=f"Proportional breakdown across top {dim2} categories.",
                x_axis=dim2,
                y_axis="count",
                data=data2,
                insight=f"'{data2[0]['category']}' accounts for {format_percentage(data2[0]['value'] / max(profile.total_rows, 1))} of records." if data2 else "",
                plotly_spec={
                    "data": [{
                        "type": "pie",
                        "labels": [d["category"] for d in data2],
                        "values": [d["value"] for d in data2],
                        "hole": 0.5
                    }],
                    "layout": {
                        "title": f"{dim2.replace('_', ' ').title()} Breakdown",
                        "template": "plotly_dark",
                        "paper_bgcolor": "rgba(0,0,0,0)"
                    }
                }
            ))

        executive_summary = (
            f"The dataset '{profile.name}' contains {profile.total_rows:,} verified rows and "
            f"{profile.total_columns} attributes with a {profile.cleaning_report.data_health_score}% health rating. "
            f"Automated data preparation resolved {profile.cleaning_report.missing_cells_imputed:,} missing cell(s) "
            f"and eliminated {profile.cleaning_report.duplicates_removed:,} duplicate(s)."
        )

        return DashboardSpec(
            dataset_id=profile.dataset_id,
            title=f"{profile.name} — Executive Overview",
            generated_at=datetime.datetime.utcnow().isoformat(),
            kpis=kpis,
            charts=charts,
            executive_summary=executive_summary
        )
