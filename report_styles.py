# CSS styles for DataMind AI Comprehensive Architectural & Technical Report

REPORT_CSS = """
@page {
  size: A4 portrait;
  margin: 14mm 14mm 14mm 14mm;
}
* {
  box-sizing: border-box;
}
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  color: #1e293b;
  background-color: #ffffff;
  margin: 0;
  padding: 0;
  font-size: 8.8pt;
  line-height: 1.42;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}

.report-page {
  height: 268mm;
  max-height: 268mm;
  page-break-after: always;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  overflow: hidden;
  padding: 0;
}

.report-page:last-child {
  page-break-after: auto;
}

/* Header & Footer */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1.5px solid #e2e8f0;
  padding-bottom: 5px;
  margin-bottom: 10px;
  font-size: 7.5pt;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.6px;
}
.page-header .brand {
  font-weight: 800;
  color: #4f46e5;
  letter-spacing: 0.8px;
}
.page-header .chapter-title {
  font-weight: 600;
  color: #334155;
}

.page-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.page-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid #e2e8f0;
  padding-top: 5px;
  margin-top: 6px;
  font-size: 7.5pt;
  color: #94a3b8;
}
.page-footer .page-number {
  font-weight: 700;
  color: #4f46e5;
}

/* Typography */
h1 {
  font-size: 16pt;
  font-weight: 800;
  color: #0f172a;
  margin: 0 0 6px 0;
  letter-spacing: -0.4px;
  line-height: 1.2;
}
h2 {
  font-size: 11.5pt;
  font-weight: 700;
  color: #1e1b4b;
  margin: 4px 0 4px 0;
  border-left: 3.5px solid #4f46e5;
  padding-left: 7px;
  line-height: 1.25;
}
h3 {
  font-size: 9.6pt;
  font-weight: 700;
  color: #334155;
  margin: 4px 0 2px 0;
}
p {
  margin: 0 0 6px 0;
  text-align: justify;
}
p:last-child {
  margin-bottom: 0;
}
strong {
  color: #0f172a;
}

/* Callout Boxes */
.callout {
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 8.4pt;
  margin: 4px 0 6px 0;
  line-height: 1.38;
}
.callout-info {
  background: #f0fdf4;
  border-left: 3.5px solid #16a34a;
  color: #166534;
}
.callout-insight {
  background: #eef2ff;
  border-left: 3.5px solid #4f46e5;
  color: #312e81;
}
.callout-warning {
  background: #fffbeb;
  border-left: 3.5px solid #d97706;
  color: #92400e;
}
.callout-tech {
  background: #f8fafc;
  border-left: 3.5px solid #0284c7;
  color: #0369a1;
}

/* Tables */
.tech-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 8pt;
  margin: 4px 0 6px 0;
}
.tech-table th {
  background: #f1f5f9;
  color: #1e293b;
  font-weight: 700;
  text-align: left;
  padding: 5px 8px;
  border: 1px solid #cbd5e1;
}
.tech-table td {
  padding: 4px 8px;
  border: 1px solid #e2e8f0;
  color: #334155;
  vertical-align: top;
}
.tech-table tr:nth-child(even) {
  background: #f8fafc;
}
.tech-table .mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 7.6pt;
  color: #0369a1;
}
.tech-table .badge {
  display: inline-block;
  padding: 1px 5px;
  border-radius: 4px;
  font-size: 7.2pt;
  font-weight: 600;
}
.badge-green { background: #dcfce7; color: #15803d; }
.badge-blue { background: #dbeafe; color: #1e40af; }
.badge-purple { background: #f3e8ff; color: #6b21a8; }
.badge-amber { background: #fef3c7; color: #92400e; }

/* Grids */
.grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin: 4px 0;
}
.grid-3 {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 8px;
  margin: 4px 0;
}
.grid-4 {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1fr;
  gap: 6px;
  margin: 4px 0;
}

/* KPI Card */
.kpi-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 6px 10px;
}
.kpi-title {
  font-size: 7.2pt;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
}
.kpi-value {
  font-size: 13pt;
  font-weight: 800;
  color: #0f172a;
  margin: 1px 0;
}
.kpi-sub {
  font-size: 7pt;
  color: #059669;
  font-weight: 600;
}

/* Architecture & Diagram Boxes */
.diagram-box {
  background: #0f172a;
  color: #e2e8f0;
  border-radius: 6px;
  padding: 8px 12px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 7.6pt;
  line-height: 1.35;
  margin: 4px 0 6px 0;
  white-space: pre;
  overflow: hidden;
}

.code-snippet {
  background: #1e293b;
  color: #f1f5f9;
  border-radius: 5px;
  padding: 7px 10px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 7.5pt;
  line-height: 1.35;
  margin: 4px 0 6px 0;
  white-space: pre-wrap;
  word-break: break-all;
}

/* Cover Page Specific Styles */
.cover-page {
  background: linear-gradient(145deg, #0f172a 0%, #1e1b4b 50%, #31104b 100%);
  color: #ffffff;
  padding: 24mm 18mm;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.cover-tag {
  display: inline-block;
  background: rgba(99, 102, 241, 0.2);
  border: 1px solid rgba(165, 180, 252, 0.4);
  color: #a5b4fc;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 8.5pt;
  font-weight: 600;
  letter-spacing: 1px;
  text-transform: uppercase;
  margin-bottom: 12px;
}
.cover-title {
  font-size: 27pt;
  font-weight: 900;
  color: #ffffff;
  line-height: 1.15;
  margin: 0 0 10px 0;
  letter-spacing: -0.6px;
}
.cover-title span {
  background: linear-gradient(90deg, #818cf8 0%, #c084fc 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.cover-subtitle {
  font-size: 11pt;
  color: #cbd5e1;
  line-height: 1.45;
  margin: 0 0 24px 0;
  max-width: 90%;
}
.cover-meta-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 14px 18px;
  margin-bottom: 24px;
}
.meta-item-label {
  font-size: 7.5pt;
  text-transform: uppercase;
  color: #94a3b8;
  letter-spacing: 0.5px;
}
.meta-item-value {
  font-size: 9pt;
  font-weight: 700;
  color: #f8fafc;
  margin-top: 2px;
}
.cover-badge-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.cover-badge {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 6px;
  padding: 6px 10px;
  font-size: 7.8pt;
  color: #e2e8f0;
}
.cover-badge strong {
  color: #c084fc;
}
"""
