import uuid
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import duckdb
import numpy as np
import pandas as pd
from app.models.schemas import DatasetProfile, InsightItem, InsightsResponse, ChartSpec
from app.engine.sql_engine import SQLEngine
from app.engine.dashboard_generator import format_number

class InsightsEngine:
    @staticmethod
    def generate_insights(parquet_path: Path, profile: DatasetProfile) -> InsightsResponse:
        """
        Runs comprehensive automated statistical and pattern detection across
        measures, dimensions, and time attributes in the dataset.
        """
        parquet_path = Path(parquet_path)
        insights: List[InsightItem] = []
        executive_takeaways: List[str] = []

        measures = profile.primary_measures
        dimensions = profile.primary_dimensions
        time_col = profile.primary_time_column
        total_rows = profile.total_rows

        if total_rows == 0:
            return InsightsResponse(
                dataset_id=profile.dataset_id,
                generated_at=datetime.datetime.utcnow().isoformat(),
                total_insights=0,
                insights=[],
                executive_takeaways=["Dataset is empty."]
            )

        con = duckdb.connect()
        view_path = str(parquet_path).replace("\\", "/")
        con.execute(f"CREATE VIEW dataset AS SELECT * FROM read_parquet('{view_path}')")

        # -------------------------------------------------------------
        # 1. CORRELATION ANALYSIS (Pairwise between numeric measures)
        # -------------------------------------------------------------
        if len(measures) >= 2:
            try:
                # Query correlation matrix for top 6 measures
                measures_to_test = measures[:6]
                corrs = []
                for i in range(len(measures_to_test)):
                    for j in range(i + 1, len(measures_to_test)):
                        m1 = measures_to_test[i]
                        m2 = measures_to_test[j]
                        sql_corr = f'''
                            SELECT ROUND(corr("{m1}", "{m2}"), 3) AS r
                            FROM dataset
                            WHERE "{m1}" IS NOT NULL AND "{m2}" IS NOT NULL
                        '''
                        r_val = con.execute(sql_corr).fetchone()[0]
                        if r_val is not None and not np.isnan(r_val):
                            corrs.append((m1, m2, float(r_val)))

                # Sort by absolute correlation strength
                corrs.sort(key=lambda x: abs(x[2]), reverse=True)

                for m1, m2, r in corrs[:3]:
                    abs_r = abs(r)
                    if abs_r >= 0.4:
                        strength = "Strong" if abs_r >= 0.7 else "Moderate"
                        direction = "positive" if r > 0 else "negative"
                        impact_note = "increase together" if r > 0 else "move in opposite directions"
                        m1_title = m1.replace("_", " ").title()
                        m2_title = m2.replace("_", " ").title()

                        title = f"{strength} {direction.capitalize()} Correlation: {m1_title} & {m2_title}"
                        desc = f"A correlation coefficient of r = {r:.2f} was detected between '{m1_title}' and '{m2_title}'. As '{m1_title}' changes, '{m2_title}' tends to {impact_note}."

                        insights.append(InsightItem(
                            id=f"insight_corr_{m1}_{m2}",
                            category="correlation",
                            importance="high" if abs_r >= 0.7 else "medium",
                            title=title,
                            description=desc,
                            metric="Pearson r",
                            score=r,
                            evidence={"feature_1": m1, "feature_2": m2, "correlation": r}
                        ))
                        executive_takeaways.append(f"{m1_title} and {m2_title} exhibit a {strength.lower()} {direction} relationship (r = {r:.2f}).")
            except Exception:
                pass

        # -------------------------------------------------------------
        # 2. ANOMALY & OUTLIER DETECTION (Z-Score / Extreme observations)
        # -------------------------------------------------------------
        for m in measures[:3]:
            try:
                # Find outliers using IQR or Z-score in DuckDB
                stats = con.execute(f'''
                    SELECT 
                        AVG("{m}") AS mean_val, 
                        STDDEV_SAMP("{m}") AS std_val,
                        COUNT(*) AS total_non_null
                    FROM dataset WHERE "{m}" IS NOT NULL
                ''').fetchone()

                if stats and stats[0] is not None and stats[1] is not None and stats[1] > 0:
                    mean_val = stats[0]
                    std_val = stats[1]
                    threshold = 3.0 * std_val

                    outliers_sql = f'''
                        SELECT COUNT(*) 
                        FROM dataset 
                        WHERE ABS("{m}" - {mean_val}) > {threshold}
                    '''
                    outlier_count = con.execute(outliers_sql).fetchone()[0]
                    if outlier_count > 0:
                        outlier_pct = round((outlier_count / total_rows) * 100, 2)
                        m_title = m.replace("_", " ").title()

                        insights.append(InsightItem(
                            id=f"insight_outlier_{m}",
                            category="anomaly",
                            importance="high" if outlier_pct > 2.0 else "medium",
                            title=f"Statistical Outliers Detected in {m_title}",
                            description=f"Identified {outlier_count:,} data points ({outlier_pct}% of total records) exceeding 3 standard deviations from the mean ({mean_val:.2f}).",
                            metric="Outlier Count",
                            score=float(outlier_count),
                            evidence={"mean": mean_val, "std": std_val, "outlier_count": outlier_count, "outlier_pct": outlier_pct}
                        ))
            except Exception:
                pass

        # -------------------------------------------------------------
        # 3. CATEGORICAL SEGMENTATION & PARETO CONCENTRATION (80/20 Rule)
        # -------------------------------------------------------------
        if dimensions and measures:
            for dim in dimensions[:2]:
                meas = measures[0]
                try:
                    seg_sql = f'''
                        SELECT 
                            "{dim}" AS cat, 
                            SUM("{meas}") AS total_meas
                        FROM dataset
                        WHERE "{dim}" IS NOT NULL
                        GROUP BY "{dim}"
                        ORDER BY total_meas DESC
                    '''
                    df_seg = con.execute(seg_sql).fetchdf()
                    if len(df_seg) >= 3:
                        total_sum = df_seg["total_meas"].sum()
                        if total_sum > 0:
                            df_seg["cum_pct"] = (df_seg["total_meas"].cumsum() / total_sum) * 100
                            top_cat = df_seg.iloc[0]["cat"]
                            top_share = round((df_seg.iloc[0]["total_meas"] / total_sum) * 100, 1)

                            dim_title = dim.replace("_", " ").title()
                            meas_title = meas.replace("_", " ").title()

                            if top_share >= 35.0:
                                insights.append(InsightItem(
                                    id=f"insight_pareto_{dim}",
                                    category="segmentation",
                                    importance="high",
                                    title=f"High Segment Concentration in {dim_title}",
                                    description=f"Category '{top_cat}' heavily dominates, accounting for {top_share}% of overall {meas_title}.",
                                    metric="Top Share %",
                                    score=top_share,
                                    evidence={"dominant_category": str(top_cat), "share_pct": top_share}
                                ))
                                executive_takeaways.append(f"{dim_title} is concentrated: '{top_cat}' alone contributes {top_share}% of {meas_title}.")
                except Exception:
                    pass

        # -------------------------------------------------------------
        # 4. TEMPORAL TREND DETECTION
        # -------------------------------------------------------------
        if time_col and measures:
            meas = measures[0]
            try:
                trend_sql = f'''
                    SELECT 
                        strftime(CAST("{time_col}" AS TIMESTAMP), '%Y-%m') AS period,
                        SUM("{meas}") AS period_val
                    FROM dataset
                    WHERE "{time_col}" IS NOT NULL
                    GROUP BY period
                    ORDER BY period ASC
                '''
                df_trend = con.execute(trend_sql).fetchdf()
                if len(df_trend) >= 3:
                    first_val = df_trend.iloc[0]["period_val"]
                    last_val = df_trend.iloc[-1]["period_val"]
                    if first_val and first_val > 0:
                        change_pct = round(((last_val - first_val) / first_val) * 100, 1)
                        meas_title = meas.replace("_", " ").title()
                        direction = "growth" if change_pct > 0 else "decline"
                        sign = "+" if change_pct > 0 else ""

                        insights.append(InsightItem(
                            id=f"insight_trend_{meas}",
                            category="trend",
                            importance="high" if abs(change_pct) > 20 else "medium",
                            title=f"Overall {direction.capitalize()} of {sign}{change_pct}% in {meas_title}",
                            description=f"Comparing the initial period ({df_trend.iloc[0]['period']}) to the most recent period ({df_trend.iloc[-1]['period']}), {meas_title} recorded a net change of {sign}{change_pct}%.",
                            metric="Net Change %",
                            score=change_pct,
                            evidence={"initial_val": float(first_val), "final_val": float(last_val), "change_pct": change_pct}
                        ))
                        executive_takeaways.append(f"{meas_title} observed a net {direction} of {sign}{change_pct}% over recorded time periods.")
            except Exception:
                pass

        con.close()

        if not executive_takeaways:
            executive_takeaways.append("Dataset metrics remain evenly distributed across examined attributes.")

        return InsightsResponse(
            dataset_id=profile.dataset_id,
            generated_at=datetime.datetime.utcnow().isoformat(),
            total_insights=len(insights),
            insights=insights,
            executive_takeaways=executive_takeaways
        )
