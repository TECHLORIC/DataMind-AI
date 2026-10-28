import os
import sys
import subprocess
import re
from pathlib import Path

from report_styles import REPORT_CSS
import report_pages_part1 as p1
import report_pages_part2 as p2
import report_pages_part3 as p3
import report_pages_part4 as p4

TOTAL_PAGES = 28

def get_header(chapter_title: str) -> str:
    return f"""
    <div class="page-header">
        <span class="brand">DataMind AI &bull; Autonomous BI Platform</span>
        <span class="chapter-title">{chapter_title}</span>
    </div>
    """

def get_footer(page_num: int) -> str:
    return f"""
    <div class="page-footer">
        <span>Confidential &bull; Engineering & Architecture Dossier</span>
        <span>DataMind AI Platform Audit v2.4</span>
        <span class="page-number">Page {page_num} of {TOTAL_PAGES}</span>
    </div>
    """

def wrap_page(page_num: int, chapter_title: str, content_html: str) -> str:
    if page_num == 1:
        return f"""
        <div class="report-page cover-page">
            {content_html}
        </div>
        """
    return f"""
    <div class="report-page">
        {get_header(chapter_title)}
        <div class="page-content">
            {content_html}
        </div>
        {get_footer(page_num)}
    </div>
    """

def generate_html() -> str:
    pages_data = [
        # Part 1: Pages 1 to 7
        (1, "Cover Page", p1.get_page_1()),
        (2, "Document Guide & Table of Contents", p1.get_page_2()),
        (3, "Chapter 1: Executive Summary & System Vision", p1.get_page_3()),
        (4, "Chapter 1.2: Enterprise Context & Market Differentiation", p1.get_page_4()),
        (5, "Chapter 2: Full-Stack System Architecture & Design", p1.get_page_5()),
        (6, "Chapter 2.2: Execution Flow & Request Lifecycle", p1.get_page_6()),
        (7, "Chapter 3: Multi-Format Data Ingestion Engine", p1.get_page_7()),

        # Part 2: Pages 8 to 14
        (8, "Chapter 3.2: Automated Data Hygiene & DataPrepAgent", p2.get_page_8()),
        (9, "Chapter 4: Dynamic Schema & Semantic Profiling", p2.get_page_9()),
        (10, "Chapter 4.2: Profiling Heuristics & Statistical Metrics", p2.get_page_10()),
        (11, "Chapter 5: High-Speed Vectorized Analytical Processing", p2.get_page_11()),
        (12, "Chapter 5.2: SQL Security Sandbox & Filter Engine", p2.get_page_12()),
        (13, "Chapter 6: Multi-Agent Orchestration & LangGraph", p2.get_page_13()),
        (14, "Chapter 6.2: Resilient Dual-Mode Execution", p2.get_page_14()),

        # Part 3: Pages 15 to 21
        (15, "Chapter 7: Conversational BI & NL-to-SQL Engine", p3.get_page_15()),
        (16, "Chapter 7.2: Zero-Hallucination Verification Pipeline", p3.get_page_16()),
        (17, "Chapter 7.3: Multilingual Analytical NLP in Practice", p3.get_page_17()),
        (18, "Chapter 8: Automated AI Insights & Discovery", p3.get_page_18()),
        (19, "Chapter 8.2: Outliers, Pareto & Temporal Trends", p3.get_page_19()),
        (20, "Chapter 9: AutoML Studio & Task Detection", p3.get_page_20()),
        (21, "Chapter 9.2: Multi-Model Competitive Leaderboard", p3.get_page_21()),

        # Part 4: Pages 22 to 28
        (22, "Chapter 9.3: Unsupervised Pattern Clustering", p4.get_page_22()),
        (23, "Chapter 9.4: Explainable AI (XAI) & What-If Simulator", p4.get_page_23()),
        (24, "Chapter 10: Modern Frontend Architecture: React 19", p4.get_page_24()),
        (25, "Chapter 10.2: Dual Dashboard Modalities", p4.get_page_25()),
        (26, "Chapter 11: Security, Scalability & Operations", p4.get_page_26()),
        (27, "Chapter 12: Gap Analysis & 24-Month Roadmap", p4.get_page_27()),
        (28, "Chapter 13: Technical Appendix & Reference", p4.get_page_28())
    ]

    rendered_pages = []
    for num, title, content in pages_data:
        rendered_pages.append(wrap_page(num, title, content))

    full_body = "\n".join(rendered_pages)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>DataMind AI &mdash; Comprehensive System Architecture & Engineering Audit Dossier</title>
    <style>
{REPORT_CSS}
    </style>
</head>
<body>
{full_body}
</body>
</html>
"""
    return html

def main():
    print("Generating comprehensive 28-page HTML report...")
    html_content = generate_html()
    html_path = Path("DataMind_AI_Comprehensive_Project_Report.html").resolve()
    html_path.write_text(html_content, encoding="utf-8")
    print(f"Saved HTML to: {html_path} ({len(html_content):,} bytes)")

    pdf_path = Path("DataMind_AI_Comprehensive_Project_Report.pdf").resolve()
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    if not Path(edge_path).exists():
        edge_path = r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"

    print(f"Compiling PDF with Edge headless: {edge_path}")
    cmd = [
        edge_path,
        "--headless=new",
        "--disable-gpu",
        "--run-all-compositor-stages-before-draw",
        "--no-pdf-header-footer",
        f"--print-to-pdf={str(pdf_path)}",
        html_path.as_uri()
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Edge execution error: {res.stderr}")
        sys.exit(1)

    if not pdf_path.exists():
        print("Error: PDF file was not generated.")
        sys.exit(1)

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    pages = len(re.findall(rb"/Type\s*/Page\b", pdf_bytes))
    size_kb = len(pdf_bytes) / 1024

    print(f"SUCCESS! Generated PDF: {pdf_path}")
    print(f"Total Page Count: {pages} pages")
    print(f"File Size: {size_kb:.1f} KB")

if __name__ == "__main__":
    main()
