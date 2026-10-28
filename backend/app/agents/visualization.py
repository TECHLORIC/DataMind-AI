from typing import Dict, Any, List, Optional
from app.models.domain.dataset import ChartSpec

class VisualizationAgent:
    """
    Visualization Agent: Automatically infers the optimal chart type
    and constructs both production Plotly JSON specifications and
    high-performance ECharts options.
    """

    @staticmethod
    def generate_chart(
        data: List[Dict[str, Any]],
        intent: str,
        title: Optional[str] = None,
        x_axis: Optional[str] = None,
        y_axis: Optional[str] = None
    ) -> Optional[ChartSpec]:
        if not data:
            return None

        # Detect keys
        first_row = data[0]
        keys = list(first_row.keys())
        cat_key = x_axis or ("category" if "category" in keys else keys[0])
        val_key = y_axis or ("value" if "value" in keys else keys[1] if len(keys) > 1 else keys[0])

        categories = [str(r.get(cat_key, "")) for r in data]
        values = [r.get(val_key, 0) for r in data]
        chart_title = title or (cat_key.replace("_", " ").title() + " Analysis")

        if intent == "temporal_trend":
            return VisualizationAgent._build_line_chart(categories, values, chart_title, cat_key, val_key, data)
        elif len(categories) <= 6 and intent != "categorical_ranking":
            return VisualizationAgent._build_pie_chart(categories, values, chart_title, cat_key, val_key, data)
        else:
            return VisualizationAgent._build_bar_chart(categories, values, chart_title, cat_key, val_key, data)

    @staticmethod
    def _build_bar_chart(categories, values, title, x_col, y_col, raw_data) -> ChartSpec:
        plotly_spec = {
            "data": [{
                "type": "bar",
                "x": categories,
                "y": values,
                "marker": {
                    "color": values,
                    "colorscale": [[0, "#6366f1"], [1, "#a855f7"]],
                    "line": {"color": "#4338ca", "width": 1}
                },
                "text": values,
                "textposition": "auto"
            }],
            "layout": {
                "title": {"text": title, "font": {"color": "#f8fafc", "size": 14}},
                "paper_bgcolor": "rgba(0,0,0,0)",
                "plot_bgcolor": "rgba(0,0,0,0)",
                "font": {"color": "#94a3b8", "family": "Inter, sans-serif"},
                "xaxis": {"gridcolor": "rgba(255,255,255,0.05)"},
                "yaxis": {"gridcolor": "rgba(255,255,255,0.05)"},
                "margin": {"l": 40, "r": 20, "t": 40, "b": 40}
            }
        }

        echarts_option = {
            "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
            "grid": {"left": "3%", "right": "4%", "bottom": "12%", "top": "12%", "containLabel": True},
            "xAxis": {"type": "category", "data": categories, "axisLabel": {"color": "#94a3b8", "rotate": 25}},
            "yAxis": {"type": "value", "splitLine": {"lineStyle": {"color": "rgba(255,255,255,0.05)"}}},
            "series": [{
                "type": "bar",
                "data": values,
                "itemStyle": {
                    "color": {
                        "type": "linear", "x": 0, "y": 0, "x2": 0, "y2": 1,
                        "colorStops": [{"offset": 0, "color": "#a855f7"}, {"offset": 1, "color": "#6366f1"}]
                    },
                    "borderRadius": [4, 4, 0, 0]
                }
            }]
        }

        return ChartSpec(
            id=f"chart_{x_col}_{y_col}",
            chart_type="bar",
            title=title,
            x_axis=x_col,
            y_axis=y_col,
            data=raw_data,
            plotly_spec=plotly_spec,
            echarts_option=echarts_option
        )

    @staticmethod
    def _build_line_chart(categories, values, title, x_col, y_col, raw_data) -> ChartSpec:
        plotly_spec = {
            "data": [{
                "type": "scatter",
                "mode": "lines+markers",
                "x": categories,
                "y": values,
                "line": {"color": "#38bdf8", "width": 3, "shape": "spline"},
                "marker": {"size": 6, "color": "#818cf8"},
                "fill": "tozeroy",
                "fillcolor": "rgba(56, 189, 248, 0.15)"
            }],
            "layout": {
                "title": {"text": title, "font": {"color": "#f8fafc", "size": 14}},
                "paper_bgcolor": "rgba(0,0,0,0)",
                "plot_bgcolor": "rgba(0,0,0,0)",
                "font": {"color": "#94a3b8"},
                "xaxis": {"gridcolor": "rgba(255,255,255,0.05)"},
                "yaxis": {"gridcolor": "rgba(255,255,255,0.05)"},
                "margin": {"l": 40, "r": 20, "t": 40, "b": 40}
            }
        }

        echarts_option = {
            "tooltip": {"trigger": "axis"},
            "grid": {"left": "3%", "right": "4%", "bottom": "10%", "top": "12%", "containLabel": True},
            "xAxis": {"type": "category", "data": categories, "axisLabel": {"color": "#94a3b8"}},
            "yAxis": {"type": "value", "splitLine": {"lineStyle": {"color": "rgba(255,255,255,0.05)"}}},
            "series": [{
                "type": "line",
                "smooth": 0.4,
                "data": values,
                "itemStyle": {"color": "#38bdf8"},
                "areaStyle": {
                    "color": {
                        "type": "linear", "x": 0, "y": 0, "x2": 0, "y2": 1,
                        "colorStops": [{"offset": 0, "color": "rgba(56, 189, 248, 0.35)"}, {"offset": 1, "color": "rgba(56, 189, 248, 0.0)"}]
                    }
                }
            }]
        }

        return ChartSpec(
            id=f"chart_trend_{x_col}",
            chart_type="line",
            title=title,
            x_axis=x_col,
            y_axis=y_col,
            data=raw_data,
            plotly_spec=plotly_spec,
            echarts_option=echarts_option
        )

    @staticmethod
    def _build_pie_chart(categories, values, title, x_col, y_col, raw_data) -> ChartSpec:
        palette = ["#a855f7", "#6366f1", "#38bdf8", "#ec4899", "#10b981", "#f59e0b"]
        plotly_spec = {
            "data": [{
                "type": "pie",
                "labels": categories,
                "values": values,
                "hole": 0.5,
                "marker": {"colors": palette[:len(categories)]},
                "textinfo": "label+percent"
            }],
            "layout": {
                "title": {"text": title, "font": {"color": "#f8fafc", "size": 14}},
                "paper_bgcolor": "rgba(0,0,0,0)",
                "font": {"color": "#94a3b8"}
            }
        }

        echarts_option = {
            "tooltip": {"trigger": "item", "formatter": "{b}: {c} ({d}%)"},
            "series": [{
                "type": "pie",
                "radius": ["45%", "72%"],
                "data": [{"name": c, "value": v} for c, v in zip(categories, values)],
                "itemStyle": {"borderRadius": 6, "borderColor": "#0f172a", "borderWidth": 2}
            }]
        }

        return ChartSpec(
            id=f"chart_pie_{x_col}",
            chart_type="donut",
            title=title,
            x_axis=x_col,
            y_axis=y_col,
            data=raw_data,
            plotly_spec=plotly_spec,
            echarts_option=echarts_option
        )
