import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
import duckdb
from app.models.schemas import DatasetProfile, ChartSpec, KPICard, DashboardSpec, FilterCondition
from app.engine.sql_engine import SQLEngine

def format_number(val: Any) -> str:
    """Format numbers into human-readable representation ($/k/M/B)."""
    if val is None:
        return "N/A"
    try:
        f = float(val)
        if abs(f) >= 1_000_000_000:
            return f"{f / 1_000_000_000:.2f}B"
        if abs(f) >= 1_000_000:
            return f"{f / 1_000_000:.2f}M"
        if abs(f) >= 1_000:
            return f"{f / 1_000:.1f}K"
        if f.is_integer():
            return f"{int(f):,}"
        return f"{f:.2f}"
    except (ValueError, TypeError):
        return str(val)

class DashboardGenerator:
    @staticmethod
    def generate_dashboard(
        parquet_path: Path,
        profile: DatasetProfile,
        filters: Optional[List[FilterCondition]] = None
    ) -> DashboardSpec:
        """
        Dynamically analyzes dataset profile and Parquet data to automatically generate
        KPI cards, comparison charts, trend charts, distributions, and relationship plots.
        """
        parquet_path = Path(parquet_path)
        kpis: List[KPICard] = []
        charts: List[ChartSpec] = []

        measures = profile.primary_measures
        dimensions = profile.primary_dimensions
        time_col = profile.primary_time_column
        total_rows = profile.total_rows

        # -------------------------------------------------------------
        # 1. GENERATE KPI CARDS
        # -------------------------------------------------------------
        # KPI 1: Total Records
        kpis.append(KPICard(
            id="kpi_total_records",
            title="Total Records",
            value=total_rows,
            formatted_value=f"{total_rows:,}",
            aggregation="count",
            measure_column="rows",
            trend_direction="neutral"
        ))

        # Additional KPIs from top measures
        for m_name in measures[:3]:
            # Get sum and average
            try:
                col_meta = next((c for c in profile.columns if c.name == m_name), None)
                agg = "sum" if not (col_meta and col_meta.cardinality_ratio > 0.05 and any(term in m_name.lower() for term in ["rate", "ratio", "pct", "percent", "avg", "age"])) else "avg"
                
                rows = SQLEngine.run_aggregate(
                    parquet_path=parquet_path,
                    measure=m_name,
                    aggregation=agg,
                    filters=filters
                )
                val = rows[0]["value"] if rows and rows[0]["value"] is not None else 0
                title_prefix = "Total" if agg == "sum" else "Average"
                pretty_name = m_name.replace("_", " ").title()

                kpis.append(KPICard(
                    id=f"kpi_{m_name}",
                    title=f"{title_prefix} {pretty_name}",
                    value=val,
                    formatted_value=format_number(val),
                    aggregation=agg,
                    measure_column=m_name,
                    trend_direction="up" if val > 0 else "neutral"
                ))
            except Exception:
                pass

        # -------------------------------------------------------------
        # 2. GENERATE COMPARISON BAR CHARTS (Dimension vs Primary Measure)
        # -------------------------------------------------------------
        if dimensions and measures:
            dim = dimensions[0]
            meas = measures[0]
            try:
                data = SQLEngine.run_aggregate(
                    parquet_path=parquet_path,
                    dimension=dim,
                    measure=meas,
                    aggregation="sum",
                    filters=filters,
                    limit=12
                )
                if data:
                    categories = [str(d["category"]) for d in data]
                    values = [d["value"] for d in data]
                    dim_title = dim.replace("_", " ").title()
                    meas_title = meas.replace("_", " ").title()

                    echarts_option = {
                        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
                        "grid": {"left": "3%", "right": "4%", "bottom": "12%", "containLabel": True},
                        "xAxis": {
                            "type": "category",
                            "data": categories,
                            "axisLabel": {"rotate": 35, "interval": 0, "color": "#9ca3af"}
                        },
                        "yAxis": {"type": "value", "axisLabel": {"color": "#9ca3af"}},
                        "series": [{
                            "name": meas_title,
                            "type": "bar",
                            "data": values,
                            "itemStyle": {
                                "color": {
                                    "type": "linear", "x": 0, "y": 0, "x2": 0, "y2": 1,
                                    "colorStops": [{"offset": 0, "color": "#6366f1"}, {"offset": 1, "color": "#4338ca"}]
                                },
                                "borderRadius": [4, 4, 0, 0]
                            }
                        }]
                    }

                    charts.append(ChartSpec(
                        id=f"chart_bar_{dim}_{meas}",
                        chart_type="bar",
                        title=f"{meas_title} by {dim_title}",
                        description=f"Comparison of {meas_title} aggregated across top {dim_title} segments.",
                        x_axis=dim,
                        y_axis=meas,
                        aggregation="sum",
                        data=data,
                        insight=f"Top category '{categories[0]}' accounts for {format_number(values[0])} of {meas_title}.",
                        echarts_option=echarts_option
                    ))
            except Exception:
                pass

        # -------------------------------------------------------------
        # 3. GENERATE TEMPORAL TREND CHART (Time vs Measure)
        # -------------------------------------------------------------
        if time_col and measures:
            meas = measures[0]
            try:
                # Query group by truncated date (DuckDB strftime / date_trunc)
                sql_trend = f'''
                    SELECT 
                        strftime(CAST("{time_col}" AS TIMESTAMP), '%Y-%m') AS category,
                        ROUND(SUM("{meas}"), 2) AS value
                    FROM dataset
                    {SQLEngine.build_where_clause(filters)}
                    WHERE "{time_col}" IS NOT NULL
                    GROUP BY category
                    ORDER BY category ASC
                    LIMIT 30
                '''
                res = SQLEngine.execute_query(parquet_path, sql_trend)
                trend_data = res["rows"]
                if trend_data and len(trend_data) > 1:
                    categories = [str(d["category"]) for d in trend_data]
                    values = [d["value"] for d in trend_data]
                    meas_title = meas.replace("_", " ").title()

                    echarts_option = {
                        "tooltip": {"trigger": "axis"},
                        "grid": {"left": "3%", "right": "4%", "bottom": "10%", "containLabel": True},
                        "xAxis": {"type": "category", "data": categories, "axisLabel": {"color": "#9ca3af"}},
                        "yAxis": {"type": "value", "axisLabel": {"color": "#9ca3af"}},
                        "series": [{
                            "name": meas_title,
                            "type": "line",
                            "smooth": True,
                            "data": values,
                            "itemStyle": {"color": "#38bdf8"},
                            "areaStyle": {
                                "color": {
                                    "type": "linear", "x": 0, "y": 0, "x2": 0, "y2": 1,
                                    "colorStops": [
                                        {"offset": 0, "color": "rgba(56, 189, 248, 0.45)"},
                                        {"offset": 1, "color": "rgba(56, 189, 248, 0.0)"}
                                    ]
                                }
                            }
                        }]
                    }

                    charts.append(ChartSpec(
                        id=f"chart_trend_{time_col}_{meas}",
                        chart_type="line",
                        title=f"{meas_title} Trend Over Time",
                        description=f"Monthly chronological trajectory of {meas_title}.",
                        x_axis=time_col,
                        y_axis=meas,
                        aggregation="sum",
                        data=trend_data,
                        insight="Temporal patterns display overall longitudinal evolution across recorded intervals.",
                        echarts_option=echarts_option
                    ))
            except Exception:
                pass

        # -------------------------------------------------------------
        # 4. GENERATE DONUT / PIE DISTRIBUTION CHART
        # -------------------------------------------------------------
        pie_dim = dimensions[1] if len(dimensions) > 1 else (dimensions[0] if dimensions else None)
        if pie_dim:
            try:
                pie_meas = measures[0] if measures else None
                data = SQLEngine.run_aggregate(
                    parquet_path=parquet_path,
                    dimension=pie_dim,
                    measure=pie_meas,
                    aggregation="sum" if pie_meas else "count",
                    filters=filters,
                    limit=7
                )
                if data and len(data) >= 2:
                    pie_title = pie_dim.replace("_", " ").title()
                    pie_series_data = [{"name": str(d["category"]), "value": d["value"]} for d in data]

                    echarts_option = {
                        "tooltip": {"trigger": "item", "formatter": "{b}: {c} ({d}%)"},
                        "legend": {"orient": "horizontal", "bottom": "0%", "textStyle": {"color": "#9ca3af"}},
                        "series": [{
                            "name": pie_title,
                            "type": "pie",
                            "radius": ["45%", "70%"],
                            "avoidLabelOverlap": False,
                            "itemStyle": {"borderRadius": 6, "borderColor": "#1f2937", "borderWidth": 2},
                            "label": {"show": False, "position": "center"},
                            "emphasis": {
                                "label": {"show": True, "fontSize": 14, "fontWeight": "bold", "color": "#f3f4f6"}
                            },
                            "data": pie_series_data
                        }]
                    }

                    charts.append(ChartSpec(
                        id=f"chart_donut_{pie_dim}",
                        chart_type="donut",
                        title=f"{pie_title} Distribution",
                        description=f"Percentage breakdown across {pie_title} segments.",
                        x_axis=pie_dim,
                        y_axis=pie_meas,
                        aggregation="sum" if pie_meas else "count",
                        data=data,
                        insight=f"'{pie_series_data[0]['name']}' is the most prominent segment.",
                        echarts_option=echarts_option
                    ))
            except Exception:
                pass

        # -------------------------------------------------------------
        # 5. GENERATE SCATTER / RELATIONSHIP PLOT (if 2+ measures exist)
        # -------------------------------------------------------------
        if len(measures) >= 2:
            m1 = measures[0]
            m2 = measures[1]
            try:
                scatter_sql = f'''
                    SELECT "{m1}" AS x, "{m2}" AS y
                    FROM dataset
                    {SQLEngine.build_where_clause(filters)}
                    WHERE "{m1}" IS NOT NULL AND "{m2}" IS NOT NULL
                    LIMIT 200
                '''
                scatter_res = SQLEngine.execute_query(parquet_path, scatter_sql)
                pts = [[r["x"], r["y"]] for r in scatter_res["rows"]]
                if pts:
                    m1_title = m1.replace("_", " ").title()
                    m2_title = m2.replace("_", " ").title()

                    echarts_option = {
                        "tooltip": {"trigger": "item", "formatter": f"{m1_title}: {{c0}}<br/>{m2_title}: {{c1}}"},
                        "grid": {"left": "3%", "right": "4%", "bottom": "10%", "containLabel": True},
                        "xAxis": {"type": "value", "name": m1_title, "axisLabel": {"color": "#9ca3af"}},
                        "yAxis": {"type": "value", "name": m2_title, "axisLabel": {"color": "#9ca3af"}},
                        "series": [{
                            "type": "scatter",
                            "symbolSize": 8,
                            "data": pts,
                            "itemStyle": {"color": "#ec4899"}
                        }]
                    }

                    charts.append(ChartSpec(
                        id=f"chart_scatter_{m1}_{m2}",
                        chart_type="scatter",
                        title=f"{m1_title} vs {m2_title}",
                        description=f"Correlation and dispersion relationship between {m1_title} and {m2_title}.",
                        x_axis=m1,
                        y_axis=m2,
                        data=[{"x": p[0], "y": p[1]} for p in pts[:50]],
                        insight="Bi-variate dispersion demonstrates underlying relationship pattern.",
                        echarts_option=echarts_option
                    ))
            except Exception:
                pass

        # -------------------------------------------------------------
        # 6. EXECUTIVE SUMMARY
        # -------------------------------------------------------------
        top_meas_text = f"Key measures analyzed include {', '.join(measures[:3])}." if measures else "No continuous numeric measures detected."
        top_dims_text = f"Primary categorical dimensions include {', '.join(dimensions[:3])}." if dimensions else "No categorical dimensions found."
        summary = (
            f"Dataset '{profile.name}' containing {total_rows:,} records across {profile.total_columns} attributes "
            f"was successfully profiled with a completeness score of {profile.completeness}%. {top_meas_text} {top_dims_text}"
        )

        return DashboardSpec(
            dataset_id=profile.dataset_id,
            title=f"{profile.name} Analytics Dashboard",
            generated_at=profile.created_at,
            kpis=kpis,
            charts=charts,
            executive_summary=summary,
            applied_filters=filters
        )
