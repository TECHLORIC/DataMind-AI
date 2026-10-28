import json
import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.models.db.database import get_db
from app.models.db.entities import DatasetRecord

router = APIRouter()

@router.get("/pdf/{dataset_id}", response_class=HTMLResponse)
async def generate_pdf_report(dataset_id: str, db: Session = Depends(get_db)):
    record = db.query(DatasetRecord).filter(DatasetRecord.id == dataset_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Dataset not found")

    profile = json.loads(record.profile_json) if record.profile_json else {}
    dashboard = json.loads(record.dashboard_json) if record.dashboard_json else {}
    cleaning = json.loads(record.cleaning_report_json) if record.cleaning_report_json else {}

    kpi_html = ""
    for k in dashboard.get("kpis", []):
        kpi_html += f"""
        <div class="kpi-card">
            <div class="kpi-title">{k.get('title')}</div>
            <div class="kpi-val">{k.get('formatted_value')}</div>
            <div class="kpi-sub">{k.get('aggregation', '').upper()} &bull; {k.get('measure_column')}</div>
        </div>
        """

    charts_html = ""
    for ch in dashboard.get("charts", [])[:4]:
        rows_html = ""
        for r in ch.get("data", [])[:6]:
            vals = list(r.values())
            c_name = vals[0] if len(vals) > 0 else ""
            c_val = vals[1] if len(vals) > 1 else ""
            rows_html += f"<tr><td>{c_name}</td><td style='text-align:right; font-weight:600;'>{c_val}</td></tr>"

        charts_html += f"""
        <div class="chart-summary">
            <h3>{ch.get('title')}</h3>
            <p class="chart-desc">{ch.get('description', '')}</p>
            <table class="data-table">
                <thead><tr><th>Category</th><th style='text-align:right;'>Value</th></tr></thead>
                <tbody>{rows_html}</tbody>
            </table>
            {f'<div class="insight-pill">&bull; {ch.get("insight")}</div>' if ch.get('insight') else ''}
        </div>
        """

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Executive BI Report - {record.name}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            color: #1e293b;
            background: #fff;
            margin: 0;
            padding: 30px;
            font-size: 13px;
            line-height: 1.5;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid #7c3aed;
            padding-bottom: 15px;
            margin-bottom: 25px;
        }}
        .brand {{
            font-size: 22px;
            font-weight: 800;
            color: #7c3aed;
        }}
        .subbrand {{
            font-size: 11px;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .meta {{
            text-align: right;
            font-size: 11px;
            color: #64748b;
        }}
        .section-title {{
            font-size: 15px;
            font-weight: 700;
            color: #0f172a;
            margin: 25px 0 12px 0;
            border-left: 4px solid #7c3aed;
            padding-left: 8px;
        }}
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 25px;
        }}
        .kpi-card {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 12px 16px;
        }}
        .kpi-title {{
            font-size: 11px;
            font-weight: 600;
            color: #64748b;
            text-transform: uppercase;
        }}
        .kpi-val {{
            font-size: 24px;
            font-weight: 800;
            color: #0f172a;
            margin: 4px 0;
        }}
        .kpi-sub {{
            font-size: 10px;
            color: #94a3b8;
        }}
        .summary-box {{
            background: #f5f3ff;
            border-left: 4px solid #8b5cf6;
            padding: 12px 16px;
            border-radius: 4px;
            font-size: 13px;
            color: #4c1d95;
            margin-bottom: 25px;
        }}
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            margin-bottom: 25px;
        }}
        .chart-summary {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 14px;
        }}
        .chart-summary h3 {{
            margin: 0 0 4px 0;
            font-size: 13px;
            color: #1e293b;
        }}
        .chart-desc {{
            margin: 0 0 10px 0;
            font-size: 11px;
            color: #64748b;
        }}
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 11px;
        }}
        .data-table th {{
            background: #e2e8f0;
            padding: 5px 8px;
            text-align: left;
            color: #475569;
        }}
        .data-table td {{
            padding: 5px 8px;
            border-bottom: 1px solid #e2e8f0;
        }}
        .insight-pill {{
            margin-top: 10px;
            font-size: 11px;
            color: #5b21b6;
            background: #ede9fe;
            padding: 4px 8px;
            border-radius: 4px;
        }}
        .print-btn {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #7c3aed;
            color: #fff;
            padding: 10px 18px;
            border-radius: 8px;
            border: none;
            font-weight: 600;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(124, 58, 237, 0.4);
        }}
        @media print {{
            .print-btn {{ display: none; }}
            body {{ padding: 0; }}
        }}
    </style>
</head>
<body>
    <button class="print-btn" onclick="window.print()">Save as PDF</button>

    <div class="header">
        <div>
            <div class="brand">DataMind AI</div>
            <div class="subbrand">Autonomous Multi-Agent BI Report</div>
        </div>
        <div class="meta">
            <div><strong>Dataset:</strong> {record.name}</div>
            <div><strong>Total Records:</strong> {record.row_count:,} &bull; <strong>Columns:</strong> {record.col_count}</div>
            <div><strong>Data Health:</strong> {cleaning.get('data_health_score', 100)}%</div>
            <div><strong>Generated:</strong> {datetime.datetime.utcnow().strftime('%B %d, %Y %H:%M UTC')}</div>
        </div>
    </div>

    <div class="summary-box">
        <strong>Executive Overview:</strong> {dashboard.get('executive_summary', 'Automated analytical summary across dataset attributes.')}
    </div>

    <div class="section-title">Key Performance Indicators</div>
    <div class="kpi-grid">
        {kpi_html}
    </div>

    <div class="section-title">Visual Breakdowns & Slices</div>
    <div class="charts-grid">
        {charts_html}
    </div>

    <script>
        window.onload = function() {{
            setTimeout(function() {{ window.print(); }}, 600);
        }};
    </script>
</body>
</html>"""
    return HTMLResponse(content=html_content)
