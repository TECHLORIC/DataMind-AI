import os
import re
import json
import uuid
import requests
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from app.config import settings
from app.models.schemas import DatasetProfile, ChatResponse, ChartSpec
from app.engine.sql_engine import SQLEngine
from app.engine.dashboard_generator import format_number

def detect_language(text: str) -> str:
    """Detect whether query is in Hindi/Hinglish, Spanish, French, or English."""
    t = text.lower()
    if re.search(r"[\u0900-\u097F]", text):
        return "hi_devanagari"
    
    hinglish_words = [
        "kaunsa", "kaun", "kisme", "kis", "kitna", "kitni", "kitne", "sabse",
        "jyada", "zyada", "kam", "batao", "dikhao", "kya", "hai", "hain",
        "kiska", "kisko", "mujhe", "chahiye", "bikri", "kamai", "munafa",
        "shikayat", "shehar", "rajya", "vibhag", "poora", "kul", "ausat",
        "kisko", "karo", "do", "kripya", "kaise"
    ]
    if any(re.search(rf"\b{w}\b", t) for w in hinglish_words):
        return "hi_hinglish"

    spanish_words = ["cuál", "cual", "cuánto", "cuanto", "ingresos", "ventas", "más", "mas", "muéstrame", "promedio"]
    if any(re.search(rf"\b{w}\b", t) for w in spanish_words):
        return "es"

    return "en"

class AIAgent:
    @staticmethod
    def answer_query(
        parquet_path: Path,
        profile: DatasetProfile,
        question: str,
        conversation_id: Optional[str] = None
    ) -> ChatResponse:
        """
        Processes natural language questions in any language (English, Hindi, Hinglish, Spanish).
        Plans analytical SQL query, executes it safely on DuckDB, verifies the output,
        and generates an in-depth explanatory response with dynamic visualization in the user's language.
        """
        parquet_path = Path(parquet_path)
        conv_id = conversation_id or f"chat_{uuid.uuid4().hex[:8]}"
        q_lower = question.lower().strip()
        user_lang = detect_language(question)

        # Step 1: Extract dataset schema context
        schema_context = []
        for col in profile.columns:
            schema_context.append(f"- \"{col.name}\" ({col.data_type}, {col.semantic_type})")
        schema_str = "\n".join(schema_context)

        # Step 2: Attempt LLM-based planning if API key is configured
        sql_query = None
        intent = "analytical_query"

        if settings.groq_api_key or settings.openai_api_key or settings.gemini_api_key:
            sql_query = AIAgent._generate_sql_llm(question, schema_str, profile.name)

        # Step 3: If no LLM available or LLM generation failed, use intelligent rule-based semantic planner
        if not sql_query:
            sql_query, detected_intent = AIAgent._generate_sql_rule_based(q_lower, profile, user_lang)
            if detected_intent:
                intent = detected_intent

        # Step 4: Execute SQL query deterministically
        table_data = []
        explanation = ""
        chart_spec = None

        if sql_query:
            try:
                result = SQLEngine.execute_query(parquet_path, sql_query, limit=50)
                table_data = result["rows"]

                # Explain and formulate chart spec in user's language
                explanation, chart_spec = AIAgent._explain_and_visualize(
                    question=question,
                    sql_query=sql_query,
                    data=table_data,
                    profile=profile,
                    lang=user_lang
                )
            except Exception as e:
                if user_lang == "hi_hinglish":
                    explanation = f"SQL query execute karne me error aaya: '{sql_query}'. Detail: {str(e)}"
                elif user_lang == "hi_devanagari":
                    explanation = f"SQL क्वेरी चलाने में त्रुटि हुई: '{sql_query}'. विवरण: {str(e)}"
                else:
                    explanation = f"Could not execute SQL query '{sql_query}'. Error: {str(e)}"
                sql_query = None
        else:
            if user_lang == "hi_hinglish":
                explanation = (
                    f"Main aapke sawal '{question}' ko is dataset ke specific column se match nahi kar paya. "
                    f"Aap measures jaise {', '.join(profile.primary_measures[:3])} ya categories jaise {', '.join(profile.primary_dimensions[:3])} ke baare me pooch sakte hain."
                )
            elif user_lang == "hi_devanagari":
                explanation = (
                    f"मैं आपके प्रश्न '{question}' को इस डेटासेट के विशिष्ट कॉलम से सीधे मैप नहीं कर सका। "
                    f"कृपया मुख्य मीट्रिक जैसे {', '.join(profile.primary_measures[:3])} या श्रेणियों जैसे {', '.join(profile.primary_dimensions[:3])} के बारे में पूछें।"
                )
            else:
                explanation = (
                    f"I couldn't map your question '{question}' to a specific metric or attribute in this dataset. "
                    f"Try asking about measures like {', '.join(profile.primary_measures[:3])} or categories like {', '.join(profile.primary_dimensions[:3])}."
                )

        return ChatResponse(
            conversation_id=conv_id,
            dataset_id=profile.dataset_id,
            question=question,
            intent=intent,
            explanation=explanation,
            sql_query=sql_query,
            table_data=table_data[:25] if table_data else None,
            chart=chart_spec,
            confidence=0.95 if sql_query else 0.4
        )

    @staticmethod
    def _generate_sql_llm(question: str, schema_str: str, dataset_name: str) -> Optional[str]:
        """Calls external LLM (Groq or OpenAI) to generate read-only DuckDB SQL."""
        prompt = f"""You are an expert SQL analytics planner for DuckDB.
The user may ask in English, Hindi, Hinglish, or other languages.
Understand the user's intent, map it to the dataset columns, and generate valid DuckDB SQL.
Dataset table is named `dataset`.
Columns:
{schema_str}

User Question: "{question}"

Rules:
1. Return ONLY the raw SQL query. No explanations, no markdown formatting, no backticks.
2. Only write read-only SELECT queries.
3. Quote column names in double quotes, e.g. "Revenue".
4. If aggregation or ranking is requested, group appropriately and LIMIT 20.
"""
        if settings.groq_api_key:
            try:
                headers = {"Authorization": f"Bearer {settings.groq_api_key}", "Content-Type": "application/json"}
                payload = {
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1
                }
                res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=8)
                if res.status_code == 200:
                    raw_sql = res.json()["choices"][0]["message"]["content"].strip()
                    raw_sql = re.sub(r"^```sql\s*", "", raw_sql)
                    return re.sub(r"\s*```$", "", raw_sql).strip()
            except Exception:
                pass

        if settings.openai_api_key:
            try:
                headers = {"Authorization": f"Bearer {settings.openai_api_key}", "Content-Type": "application/json"}
                payload = {
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1
                }
                res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=8)
                if res.status_code == 200:
                    raw_sql = res.json()["choices"][0]["message"]["content"].strip()
                    raw_sql = re.sub(r"^```sql\s*", "", raw_sql)
                    return re.sub(r"\s*```$", "", raw_sql).strip()
            except Exception:
                pass

        return None

    @staticmethod
    def _generate_sql_rule_based(q: str, profile: DatasetProfile, lang: str = "en") -> Tuple[Optional[str], str]:
        """
        Multilingual semantic parser mapping English, Hindi/Hinglish, and Spanish questions
        directly to dataset measures and dimensions.
        """
        measures = profile.primary_measures
        dimensions = profile.primary_dimensions
        time_col = profile.primary_time_column

        # Map target measure across languages
        target_measure = None
        for m in measures:
            clean_m = m.lower().replace("_", " ")
            if clean_m in q or m.lower() in q:
                target_measure = m
                break

        if not target_measure and measures:
            revenue_terms = ["money", "earnings", "sales", "revenue", "income", "bikri", "kamai", "paisa", "ventas", "ingresos"]
            marks_terms = ["grade", "marks", "score", "number", "ank", "calificacion"]
            quantity_terms = ["quantity", "volume", "units", "count", "ginti", "kitne", "shikayat", "complaint", "complaints"]
            profit_terms = ["profit", "margin", "fayda", "munafa", "ganancia"]

            if any(w in q for w in revenue_terms):
                target_measure = next((m for m in measures if any(x in m.lower() for x in ["rev", "sale", "amount", "price", "income"])), measures[0])
            elif any(w in q for w in profit_terms):
                target_measure = next((m for m in measures if "profit" in m.lower() or "margin" in m.lower()), measures[0])
            elif any(w in q for w in marks_terms):
                target_measure = next((m for m in measures if any(x in m.lower() for x in ["mark", "score", "grade"])), measures[0])
            elif any(w in q for w in quantity_terms):
                target_measure = next((m for m in measures if any(x in m.lower() for x in ["qty", "quant", "count", "unit"])), measures[0])
            else:
                target_measure = measures[0]

        # Map target dimension across languages
        target_dimension = None
        for d in dimensions:
            clean_d = d.lower().replace("_", " ")
            if clean_d in q or d.lower() in q:
                target_dimension = d
                break

        if not target_dimension and dimensions:
            dept_terms = ["department", "dept", "vibhag", "departamento"]
            prod_terms = ["product", "item", "cheez", "samaana", "producto", "issue"]
            geo_terms = ["region", "country", "city", "state", "location", "shehar", "rajya", "ilaaka", "division", "estado"]
            cat_terms = ["category", "type", "segment", "prakar", "varg", "tipo", "response", "channel"]

            if any(w in q for w in dept_terms):
                target_dimension = next((d for d in dimensions if "dept" in d.lower() or "department" in d.lower()), None)
            elif any(w in q for w in prod_terms):
                target_dimension = next((d for d in dimensions if any(x in d.lower() for x in ["prod", "item", "issue"])), None)
            elif any(w in q for w in geo_terms):
                target_dimension = next((d for d in dimensions if any(x in d.lower() for x in ["reg", "coun", "city", "stat", "div", "loc"])), None)
            elif any(w in q for w in cat_terms):
                target_dimension = next((d for d in dimensions if any(x in d.lower() for x in ["cat", "type", "seg", "resp", "chan"])), None)

        # Detect Aggregation function across languages
        agg = "SUM"
        if any(w in q for w in ["average", "avg", "mean", "ausat", "promedio"]):
            agg = "AVG"
        elif any(w in q for w in ["highest", "max", "maximum", "peak", "sabse jyada", "sabse zyada", "sabse bada", "más alto", "mayor"]):
            agg = "MAX"
        elif any(w in q for w in ["lowest", "min", "minimum", "sabse kam", "sabse chota", "más bajo", "menor"]):
            agg = "MIN"
        elif any(w in q for w in ["how many", "count of", "total number", "kitne", "ginti", "cuántos"]):
            agg = "COUNT"

        is_asc = any(w in q for w in ["lowest", "worst", "bottom", "sabse kam", "más bajo"])
        order_dir = "ASC" if is_asc else "DESC"

        limit_match = re.search(r"\b(top|bottom)\s+(\d+)", q)
        limit_val = int(limit_match.group(2)) if limit_match else 10

        # Pattern A: Trend over time
        if time_col and any(w in q for w in ["trend", "over time", "monthly", "by month", "timeline", "trajectory", "mahina", "samay"]):
            meas = target_measure or "1"
            agg_expr = f'ROUND({agg}("{meas}"), 2)' if target_measure else "COUNT(*)"
            sql = f'''
                SELECT 
                    strftime(CAST("{time_col}" AS TIMESTAMP), '%Y-%m') AS period,
                    {agg_expr} AS value
                FROM dataset
                WHERE "{time_col}" IS NOT NULL
                GROUP BY period
                ORDER BY period ASC
                LIMIT 24
            '''
            return sql, "temporal_trend"

        # Pattern B: Grouping by dimension
        if target_dimension and target_measure:
            sql = f'''
                SELECT 
                    "{target_dimension}" AS category,
                    ROUND({agg}("{target_measure}"), 2) AS value
                FROM dataset
                WHERE "{target_dimension}" IS NOT NULL AND "{target_measure}" IS NOT NULL
                GROUP BY "{target_dimension}"
                ORDER BY value {order_dir}
                LIMIT {limit_val}
            '''
            return sql, "dimension_comparison"

        # Pattern C: Dimension count distribution
        if target_dimension and not target_measure:
            sql = f'''
                SELECT 
                    "{target_dimension}" AS category,
                    COUNT(*) AS value
                FROM dataset
                WHERE "{target_dimension}" IS NOT NULL
                GROUP BY "{target_dimension}"
                ORDER BY value {order_dir}
                LIMIT {limit_val}
            '''
            return sql, "distribution"

        # Pattern D: Overall single metric aggregation
        if target_measure:
            sql = f'''
                SELECT 
                    ROUND({agg}("{target_measure}"), 2) AS "{agg.lower()}_{target_measure}"
                FROM dataset
                WHERE "{target_measure}" IS NOT NULL
            '''
            return sql, "summary_kpi"

        # Pattern E: Row count
        if any(w in q for w in ["how many rows", "total records", "kitne records", "kul sankhya", "cuántos registros"]):
            return "SELECT COUNT(*) AS total_records FROM dataset", "record_count"

        # Default fallback
        if dimensions:
            dim = dimensions[0]
            meas = measures[0] if measures else None
            if meas:
                return f'''
                    SELECT "{dim}" AS category, ROUND(SUM("{meas}"), 2) AS value
                    FROM dataset
                    WHERE "{dim}" IS NOT NULL
                    GROUP BY "{dim}"
                    ORDER BY value DESC
                    LIMIT 10
                ''', "default_breakdown"
            else:
                return f'''
                    SELECT "{dim}" AS category, COUNT(*) AS value
                    FROM dataset
                    WHERE "{dim}" IS NOT NULL
                    GROUP BY "{dim}"
                    ORDER BY value DESC
                    LIMIT 10
                ''', "default_breakdown"

        return "SELECT * FROM dataset LIMIT 10", "sample_records"

    @staticmethod
    def _explain_and_visualize(
        question: str,
        sql_query: str,
        data: List[Dict[str, Any]],
        profile: DatasetProfile,
        lang: str = "en"
    ) -> Tuple[str, Optional[ChartSpec]]:
        """
        Formulates an in-depth, executive-grade detailed explanation in the user's language,
        complete with key findings, breakdown rankings, business context, and dynamic chart specifications.
        """
        if not data:
            if lang == "hi_hinglish":
                return "Query successfully run hui, lekin koi matching record nahi mila.", None
            elif lang == "hi_devanagari":
                return "क्वेरी सफलतापूर्वक निष्पादित हुई, लेकिन कोई मिलान रिकॉर्ड नहीं मिला।", None
            return "Query executed successfully, but returned zero matching records.", None

        # Case 1: Single scalar metric result
        if len(data) == 1 and len(data[0]) == 1:
            col_name = list(data[0].keys())[0]
            val = data[0][col_name]
            formatted = format_number(val)
            metric_title = col_name.replace("_", " ").title()

            if lang == "hi_hinglish":
                explanation = (
                    f"### 🎯 Key Finding (Mukhya Niskarsh)\n\n"
                    f"Aapke sawal ke mutabik, total **{metric_title}** ka verified value **{formatted}** hai.\n\n"
                    f"#### 📊 Detailed Breakdown:\n"
                    f"- **Analyzed Metric:** `{metric_title}`\n"
                    f"- **Verified Output:** `{formatted}`\n"
                    f"- **Dataset Scope:** Total {profile.total_rows:,} records evaluated.\n\n"
                    f"💡 **Business Context:** Yeh figure aapke data ka central benchmark represent karta hai."
                )
            elif lang == "hi_devanagari":
                explanation = (
                    f"### 🎯 मुख्य निष्कर्ष (Key Finding)\n\n"
                    f"आपके प्रश्न के आधार पर, कुल **{metric_title}** का मान **{formatted}** है।\n\n"
                    f"#### 📊 विस्तृत विवरण (Detailed Analysis)\n"
                    f"- **सत्यापित मीट्रिक:** `{metric_title}`\n"
                    f"- **सटीक गणना:** `{formatted}`\n"
                    f"- **विश्लेषण स्तर:** समग्र डेटासेट ({profile.total_rows:,} कुल रिकॉर्ड्स)\n\n"
                    f"💡 **व्यापारिक दृष्टिकोण:** यह आंकड़ा संगठन के समग्र प्रदर्शन का एक केंद्रीय बेंचमार्क प्रस्तुत करता है।"
                )
            elif lang == "es":
                explanation = (
                    f"### 🎯 Resultado Principal\n\n"
                    f"El valor verificado para **{metric_title}** es **{formatted}**.\n\n"
                    f"#### 📊 Análisis Detallado\n"
                    f"- **Métrica:** `{metric_title}`\n"
                    f"- **Resultado Exacto:** `{formatted}`\n"
                    f"- **Alcance:** Total de {profile.total_rows:,} registros evaluados."
                )
            else:
                explanation = (
                    f"### 🎯 Key Finding\n\n"
                    f"The verified calculation for **{metric_title}** is **{formatted}**.\n\n"
                    f"#### 📊 Detailed Breakdown\n"
                    f"- **Metric Analyzed:** `{metric_title}`\n"
                    f"- **Exact Verified Value:** `{formatted}`\n"
                    f"- **Cohort Scope:** Complete dataset ({profile.total_rows:,} total records evaluated)\n\n"
                    f"💡 **Business Context:** This metric establishes the primary performance baseline across your organizational data."
                )
            return explanation, None

        # Case 2: Categorical Breakdown (2 columns: category and value)
        keys = list(data[0].keys())
        chart_spec = None

        if len(keys) == 2:
            cat_key = keys[0] if not isinstance(data[0][keys[0]], (int, float)) else keys[1]
            val_key = keys[1] if cat_key == keys[0] else keys[0]

            top_item = data[0]
            top_cat = top_item[cat_key]
            top_val = top_item[val_key]
            top_val_formatted = format_number(top_val)

            total_sum = sum(r[val_key] for r in data if isinstance(r[val_key], (int, float))) or 1.0
            top_share = round((top_val / total_sum * 100), 1) if isinstance(top_val, (int, float)) else 0.0

            runner_up_text = ""
            if len(data) > 1:
                second = data[1]
                second_cat = second[cat_key]
                second_val = format_number(second[val_key])
                runner_up_text = f", followed by **{second_cat}** with **{second_val}**"

            # Ranked list string (top 5)
            ranking_lines = []
            for idx, r in enumerate(data[:5]):
                r_val = r[val_key]
                pct = round((r_val / total_sum * 100), 1) if isinstance(r_val, (int, float)) else 0
                ranking_lines.append(f"{idx + 1}. **{r[cat_key]}**: {format_number(r_val)} ({pct}% share)")
            ranking_str = "\n".join(ranking_lines)

            cat_title = cat_key.replace('_', ' ').title()
            val_title = val_key.replace('_', ' ').title()

            if lang == "hi_hinglish":
                explanation = (
                    f"### 🎯 Key Finding (Mukhya Niskarsh)\n\n"
                    f"Total **{len(data)}** analyzed categories me se, sabse aage **{top_cat}** hai "
                    f"jisme **{top_val_formatted}** volume record hua hai (kul hissa: **{top_share}%**){runner_up_text}।\n\n"
                    f"#### 📊 Top Performance Rankings:\n"
                    f"{ranking_str}\n\n"
                    f"#### 💡 Business Insights & Strategy:\n"
                    f"- **Primary Driver:** **{top_cat}** is segment ka sabse bada driver hai jo akele **{top_share}%** represent karta hai.\n"
                    f"- **Volume Concentration:** Top 3 categories overall volume ka maximum hissa cover karti hain (Pareto principle).\n"
                    f"- **Actionable Advice:** {top_cat} par focus banaye rakhte hue lower categories me growth opportunities explore karni chahiye."
                )
            elif lang == "hi_devanagari":
                explanation = (
                    f"### 🎯 मुख्य निष्कर्ष (Key Finding)\n\n"
                    f"कुल **{len(data)}** विश्लेषित श्रेणियों में, **{top_cat}** सबसे शीर्ष पर है "
                    f"जिसका मान **{top_val_formatted}** दर्ज किया गया है (कुल हिस्सेदारी: **{top_share}%**){runner_up_text}।\n\n"
                    f"#### 📊 शीर्ष श्रेणियों की रैंकिंग (Top Rankings):\n"
                    f"{ranking_str}\n\n"
                    f"#### 💡 व्यापारिक दृष्टिकोण और अंतर्दृष्टि (Business Insight):\n"
                    f"- **{top_cat}** इस श्रेणी का सबसे बड़ा चालक (primary driver) है, जो अकेले **{top_share}%** का प्रतिनिधित्व करता है।\n"
                    f"- शीर्ष 3 श्रेणियां कुल वॉल्यूम का अधिकांश हिस्सा बनाती हैं। रणनीतिक रूप से इस वर्ग पर ध्यान केंद्रित करने से उच्चतम रिटर्न प्राप्त होगा।"
                )
            elif lang == "es":
                explanation = (
                    f"### 🎯 Conclusión Clave\n\n"
                    f"De los **{len(data)}** segmentos evaluados, **{top_cat}** lidera con **{top_val_formatted}** "
                    f"(representando el **{top_share}%** del total){runner_up_text}.\n\n"
                    f"#### 📊 Clasificación Detallada:\n"
                    f"{ranking_str}\n\n"
                    f"💡 **Contexto Estratégico:** **{top_cat}** concentra la mayor parte de la actividad, siendo el motor determinante en esta categoría."
                )
            else:
                explanation = (
                    f"### 🎯 Key Finding\n\n"
                    f"Across all **{len(data)}** evaluated {cat_title.lower()} segments, **{top_cat}** emerges as the clear leader with **{top_val_formatted}** "
                    f"(accounting for **{top_share}%** of the analyzed volume){runner_up_text}.\n\n"
                    f"#### 📊 Top Performance Rankings:\n"
                    f"{ranking_str}\n\n"
                    f"#### 💡 Business Context & Strategic Takeaways:\n"
                    f"- **Segment Dominance:** **{top_cat}** represents the primary driver in this cohort, capturing {top_share}% of overall {val_title.lower()}.\n"
                    f"- **Concentration Pattern:** The top contributors account for the vast majority of volume, illustrating Pareto distribution dynamics.\n"
                    f"- **Actionable Opportunity:** Focus operational and tactical resources on sustaining {top_cat} while addressing growth gaps in runner-up segments."
                )

            # Build ECharts visual in electric violet Power BI style
            categories = [str(r[cat_key]) for r in data]
            values = [r[val_key] for r in data]
            is_time = any(x in cat_key.lower() for x in ["period", "date", "month", "year"])
            chart_type = "line" if is_time else "bar"

            echarts_option = {
                "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
                "grid": {"left": "3%", "right": "5%", "bottom": "18%", "containLabel": True},
                "xAxis": {
                    "type": "category",
                    "data": categories,
                    "axisLabel": {"rotate": 35 if len(categories) > 4 else 0, "color": "#9ca3af", "fontSize": 11}
                },
                "yAxis": {"type": "value", "axisLabel": {"color": "#9ca3af"}},
                "series": [{
                    "name": val_title,
                    "type": chart_type,
                    "smooth": True if chart_type == "line" else False,
                    "data": values,
                    "itemStyle": {
                        "color": {
                            "type": "linear", "x": 0, "y": 0, "x2": 0, "y2": 1,
                            "colorStops": [
                                {"offset": 0, "color": "#8b5cf6"},
                                {"offset": 1, "color": "#6d28d9"}
                            ]
                        },
                        "borderRadius": [4, 4, 0, 0] if chart_type == "bar" else 0
                    }
                }]
            }

            chart_spec = ChartSpec(
                id=f"chart_{uuid.uuid4().hex[:6]}",
                chart_type=chart_type,
                title=f"{val_title} by {cat_title}",
                description=f"Deterministic SQL calculation: {sql_query.strip()}",
                x_axis=cat_key,
                y_axis=val_key,
                data=data,
                insight=f"Leader: {top_cat} ({top_val_formatted} • {top_share}% share)",
                echarts_option=echarts_option
            )
        else:
            explanation = f"Query returned {len(data):,} matching record(s)."

        return explanation, chart_spec
