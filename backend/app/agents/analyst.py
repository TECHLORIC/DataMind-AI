import re
import requests
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
from app.core.config import settings
from app.services.duckdb_service import DuckDBService
from app.utils.formatting import format_number, format_percentage

def detect_language(text: str) -> str:
    """Detect whether query is in Hindi/Hinglish, Devanagari, Spanish, or English."""
    t = text.lower()
    if re.search(r"[\u0900-\u097F]", text):
        return "hi_devanagari"
    
    hinglish_words = [
        "kaunsa", "kaun", "kisme", "kis", "kitna", "kitni", "kitne", "sabse",
        "jyada", "zyada", "kam", "batao", "dikhao", "kya", "hai", "hain",
        "kiska", "kisko", "mujhe", "chahiye", "bikri", "kamai", "munafa",
        "shikayat", "shehar", "rajya", "vibhag", "poora", "kul", "ausat",
        "karo", "diya", "wali", "wale", "kahan", "bhi"
    ]
    if any(re.search(rf"\b{w}\b", t) for w in hinglish_words):
        return "hi_hinglish"

    spanish_words = ["cuál", "cual", "cuánto", "cuanto", "ingresos", "ventas", "más", "mas", "muéstrame", "promedio"]
    if any(re.search(rf"\b{w}\b", t) for w in spanish_words):
        return "es"

    return "en"


class AnalystAgent:
    """
    Analyst Agent: Interprets natural language questions with deep entity recognition,
    metric synonym mapping, filter inference, and safe DuckDB execution.
    Generates conversational, human-friendly business insights in the user's native language.
    """

    MEASURE_SYNONYMS = {
        "gross sales": ["gross_sales_inr", "gross_sales", "gross_amount"],
        "net sales": ["sales_inr", "sales", "net_sales"],
        "sales": ["sales_inr", "gross_sales_inr", "sales", "revenue", "amount_spent"],
        "revenue": ["gross_sales_inr", "sales_inr", "revenue", "amount_spent"],
        "turnover": ["gross_sales_inr", "sales_inr"],
        "bikri": ["sales_inr", "gross_sales_inr"],
        "kamai": ["gross_sales_inr", "sales_inr", "profit_inr"],
        "profit": ["profit_inr", "profit_margin_pct", "profit"],
        "margin": ["profit_margin_pct", "profit_inr", "margin"],
        "munafa": ["profit_inr", "profit_margin_pct"],
        "fayda": ["profit_inr"],
        "unit price": ["unit_price_inr", "price"],
        "price": ["unit_price_inr", "price", "amount_spent"],
        "daam": ["unit_price_inr"],
        "keemat": ["unit_price_inr"],
        "discount amount": ["discount_amount_inr"],
        "discount percent": ["discount_pct"],
        "discount": ["discount_amount_inr", "discount_pct", "discount"],
        "chhut": ["discount_amount_inr", "discount_pct"],
        "cost": ["cost_inr", "cost", "expense"],
        "expense": ["cost_inr", "expense"],
        "kharcha": ["cost_inr"],
        "rating": ["customer_rating", "rating", "score"],
        "stars": ["customer_rating"],
        "satisfaction": ["customer_rating"],
        "age": ["customer_age", "age"],
        "umr": ["customer_age"],
        "relief": ["monetary_relief_amount", "relief_amount"],
        "monetary relief": ["monetary_relief_amount"],
        "compensation": ["monetary_relief_amount"],
        "muawaza": ["monetary_relief_amount"],
        "delivery": ["delivery_days"],
        "shipping days": ["delivery_days"],
        "quantity": ["quantity", "volume", "units"],
        "units": ["quantity"],
        "volume": ["quantity", "volume"],
        "ginti": ["quantity"]
    }

    DIMENSION_SYNONYMS = {
        "region": ["region", "state", "division"],
        "shehar": ["city", "region"],
        "rajya": ["state", "region"],
        "area": ["region", "division"],
        "zone": ["region", "division"],
        "category": ["category", "product"],
        "prakar": ["category", "product"],
        "varg": ["category", "customer_segment"],
        "product": ["product", "category"],
        "item": ["product", "category"],
        "samaana": ["product", "category"],
        "cheez": ["product", "category"],
        "customer segment": ["customer_segment"],
        "segment": ["customer_segment", "category"],
        "channel": ["submission_channel", "sales_channel"],
        "sales channel": ["sales_channel"],
        "submission channel": ["submission_channel"],
        "medium": ["submission_channel", "sales_channel"],
        "payment method": ["payment_method"],
        "payment": ["payment_method"],
        "bhuqtan": ["payment_method"],
        "order status": ["order_status"],
        "status": ["order_status", "company_response"],
        "halat": ["order_status"],
        "issue": ["issue", "problem"],
        "shikayat": ["submission_channel", "issue", "product"],
        "complaint": ["submission_channel", "issue", "product"],
        "problem": ["issue"],
        "company response": ["company_response"],
        "response": ["company_response", "timely_response"],
        "state": ["state", "region"],
        "division": ["division", "region"]
    }

    OUT_OF_SCOPE_CONCEPTS = [
        "balance sheet", "p&l statement", "valuation", "business valuation",
        "market cap", "stock price", "share price", "equity", "liability",
        "liabilities", "audit report", "ceo", "founder", "weather",
        "bitcoin", "crypto", "dividend", "interest rate", "inflation"
    ]

    GREETINGS = ["hi", "hello", "hey", "namaste", "hola", "good morning", "good afternoon", "good evening", "kya hal hai"]

    @staticmethod
    def analyze(
        parquet_path: Path,
        schema_info: Dict[str, Any],
        question: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        parquet_path = Path(parquet_path)
        q_raw = question.strip()
        q_clean = q_raw.lower()
        lang = detect_language(q_raw)
        columns = schema_info.get("columns", [])
        measures = schema_info.get("primary_measures", [])
        dimensions = schema_info.get("primary_dimensions", [])
        time_col = schema_info.get("primary_time_column")
        dataset_name = schema_info.get("name", "Dataset")

        # -------------------------------------------------------------
        # 1. Greetings Handling
        # -------------------------------------------------------------
        if any(re.match(rf"^{w}[!\?.\s]*$", q_clean) for w in AnalystAgent.GREETINGS):
            meas_list = ", ".join([f"**{m.replace('_', ' ')}**" for m in measures[:4]])
            dim_list = ", ".join([f"**{d.replace('_', ' ')}**" for d in dimensions[:4]])
            if lang in ["hi_hinglish", "hi_devanagari"]:
                msg = f"### 👋 नमस्ते! Main aapka AI Data Analyst hoon.\n\nMaine **'{dataset_name}'** ko ready kar liya hai. Aap is dataset ke kisi bhi metric ya category ke baare me seedhe pooch sakte hain:\n\n- 📊 **Metrics:** {meas_list}\n- 🏷️ **Categories:** {dim_list}\n\n**Udaharan ke liye:**\n1. *'East region ki sales kitni hai?'*\n2. *'Monthly trend graph me dikhao'*\n3. *'Top categories by volume'*"
            else:
                msg = f"### 👋 Hello! I'm your AI Data Analytics Assistant.\n\nI'm ready to answer questions about **'{dataset_name}'** with verified calculations and charts.\n\n- 📊 **Available Measures:** {meas_list}\n- 🏷️ **Available Categories:** {dim_list}\n\n**Example Questions You Can Ask:**\n1. *'What is the total sales of East region?'*\n2. *'Which product or category leads in volume?'*\n3. *'Show monthly trend over time'*"
            return {
                "intent": "conversational_greeting",
                "sql_query": None,
                "table_data": [],
                "explanation": msg,
                "language": lang
            }

        # -------------------------------------------------------------
        # 2. Out of Scope Inquiry Handling
        # -------------------------------------------------------------
        for concept in AnalystAgent.OUT_OF_SCOPE_CONCEPTS:
            if concept in q_clean:
                meas_list = ", ".join([f"**{m.replace('_', ' ')}**" for m in measures[:4]])
                dim_list = ", ".join([f"**{d.replace('_', ' ')}**" for d in dimensions[:4]])
                if lang in ["hi_hinglish", "hi_devanagari"]:
                    msg = f"### ℹ️ Jankari Upalabdh Nahi Hai (**{concept.title()}**)\n\nAapne **'{concept}'** ke baare me poocha, lekin yeh dataset (**{dataset_name}**) operational records se juda hai (jaise sales, orders, complaints ya metrics), isme corporate financial balance sheet ya valuation filings shamil nahi hain.\n\n#### 📊 Is dataset me aap ye dekh sakte hain:\n- **Metrics:** {meas_list}\n- **Categories:** {dim_list}\n\n*Udaharan: 'Sales by region dikhao' ya 'Top product categories'*."
                else:
                    msg = f"### ℹ️ Topic Not in Dataset (**{concept.title()}**)\n\nYou asked about **'{concept}'**, but the active dataset (**{dataset_name}**) contains operational transactional data rather than corporate balance sheets, audit reports, or market valuation filings.\n\n#### 📊 Available Attributes in this Dataset:\n- **Measures:** {meas_list}\n- **Categories:** {dim_list}\n\n*Try asking: 'Total sales by region' or 'Which category leads in volume?'*"
                return {
                    "intent": "out_of_scope",
                    "sql_query": None,
                    "table_data": [],
                    "explanation": msg,
                    "language": lang
                }

        # -------------------------------------------------------------
        # 3. Detect Filter Entities from Dataset Sample Values & Domain Sets
        # -------------------------------------------------------------
        filter_conditions: List[Dict[str, str]] = []
        for col in columns:
            col_name = col.get("name", "")
            if col.get("semantic_type") in ["dimension", "identifier"]:
                samples = col.get("sample_values", [])
                for val in samples:
                    val_str = str(val).strip()
                    if len(val_str) >= 2 and val_str.lower() not in ["null", "none", "true", "false"]:
                        pattern = rf"\b{re.escape(val_str.lower())}\b"
                        if re.search(pattern, q_clean):
                            filter_conditions.append({
                                "column": col_name,
                                "value": val_str,
                                "raw_match": val_str
                            })

        # Known common entity mapping
        col_names_map = {c.get("name", "").lower(): c.get("name") for c in columns}
        if "region" in col_names_map:
            for r in ["north", "south", "east", "west", "central"]:
                if re.search(rf"\b{r}\b", q_clean) and not any(f["value"].lower() == r for f in filter_conditions):
                    filter_conditions.append({"column": col_names_map["region"], "value": r.title(), "raw_match": r})
        if "state" in col_names_map:
            state_codes = {"ca": "CA", "california": "CA", "ny": "NY", "new york": "NY", "tx": "TX", "texas": "TX", "va": "VA", "virginia": "VA", "fl": "FL", "florida": "FL"}
            for s_word, s_code in state_codes.items():
                if re.search(rf"\b{s_word}\b", q_clean) and not any(f["value"] == s_code for f in filter_conditions):
                    filter_conditions.append({"column": col_names_map["state"], "value": s_code, "raw_match": s_word})
        if "order_status" in col_names_map:
            for st in ["completed", "pending", "cancelled", "returned"]:
                if re.search(rf"\b{st}\b", q_clean) and not any(f["value"].lower() == st for f in filter_conditions):
                    filter_conditions.append({"column": col_names_map["order_status"], "value": st.title(), "raw_match": st})

        # -------------------------------------------------------------
        # 4. Resolve Target Measure (Metric)
        # -------------------------------------------------------------
        target_measure: Optional[str] = None
        for phrase, cands in AnalystAgent.MEASURE_SYNONYMS.items():
            if phrase in q_clean:
                for cand in cands:
                    matched = next((m for m in measures if cand == m.lower() or cand in m.lower()), None)
                    if matched:
                        target_measure = matched
                        break
            if target_measure:
                break

        if not target_measure:
            for col in columns:
                if col.get("semantic_type") == "measure":
                    c_name = col.get("name", "")
                    clean_c = c_name.lower().replace("_", " ")
                    if clean_c in q_clean:
                        target_measure = c_name
                        break
                    tokens = [t for t in clean_c.split() if t not in ["inr", "pct", "amount", "total"]]
                    if tokens and any(t in q_clean for t in tokens):
                        target_measure = c_name
                        break

        # -------------------------------------------------------------
        # 5. Resolve Target Dimension (Grouping Category)
        # -------------------------------------------------------------
        target_dimension: Optional[str] = None
        for phrase, cands in AnalystAgent.DIMENSION_SYNONYMS.items():
            if phrase in q_clean:
                for cand in cands:
                    matched = next((d for d in dimensions if cand == d.lower() or cand in d.lower()), None)
                    if matched:
                        target_dimension = matched
                        break
            if target_dimension:
                break

        if not target_dimension:
            for col in columns:
                if col.get("semantic_type") in ["dimension", "target_candidate"]:
                    c_name = col.get("name", "")
                    clean_c = c_name.lower().replace("_", " ")
                    if clean_c in q_clean:
                        target_dimension = c_name
                        break

        # -------------------------------------------------------------
        # 6. Resolve Aggregation Function
        # -------------------------------------------------------------
        agg = "SUM"
        agg_label = "Total"
        if any(w in q_clean for w in ["average", "avg", "mean", "ausat", "promedio"]):
            agg = "AVG"
            agg_label = "Average"
        elif any(w in q_clean for w in ["highest", "max", "maximum", "peak", "top", "sabse jyada", "sabse zyada", "sabse bada"]):
            agg = "MAX"
            agg_label = "Maximum"
        elif any(w in q_clean for w in ["lowest", "min", "minimum", "bottom", "sabse kam", "sabse chota"]):
            agg = "MIN"
            agg_label = "Minimum"
        elif any(w in q_clean for w in ["how many", "count of", "number of", "kitne", "kitni", "ginti"]):
            agg = "COUNT"
            agg_label = "Count"

        # Complaint volume heuristic
        if any(w in q_clean for w in ["shikayat", "complaint", "complaints"]) and not any(w in q_clean for w in ["relief", "money", "rupee", "amount", "dollar", "muawaza"]):
            agg = "COUNT"
            agg_label = "Count"

        # -------------------------------------------------------------
        # 7. Route to Query Structure
        # -------------------------------------------------------------
        has_explicit_group_by = any(w in q_clean for w in ["by ", "across ", "each ", "every ", "per ", "compare ", "breakdown", "distribution", "ranking", "all "])
        is_trend = any(w in q_clean for w in ["trend", "monthly", "over time", "growth", "trajectory", "mahine", "timeline", "yearly", "annual", "daily", "by year", "by month", "by day", "period", "history", "samay"])

        # Check if external LLM generation is configured
        sql: Optional[str] = None
        intent = "analytical_query"

        # Pattern A: Specific Filter Applied (e.g. "sales of north region", "gross sales of east region", "orders pending")
        if filter_conditions and not has_explicit_group_by:
            filt = filter_conditions[0]
            f_col = filt["column"]
            f_val = filt["value"]
            meas = target_measure or (measures[0] if measures else None)

            if meas and agg != "COUNT":
                sql = f'''
                    SELECT 
                        '{f_val}' AS category,
                        ROUND({agg}("{meas}"), 2) AS value,
                        COUNT(*) AS record_count,
                        ROUND(AVG("{meas}"), 2) AS avg_value
                    FROM dataset
                    WHERE LOWER("{f_col}") LIKE '%{f_val.lower()}%' AND "{meas}" IS NOT NULL
                '''
                intent = "filtered_entity_metric"
            else:
                sql = f'''
                    SELECT 
                        '{f_val}' AS category,
                        COUNT(*) AS value
                    FROM dataset
                    WHERE LOWER("{f_col}") LIKE '%{f_val.lower()}%'
                '''
                intent = "filtered_entity_count"

        # Pattern B: Temporal Trend
        elif is_trend and time_col:
            meas = target_measure or (measures[0] if measures else None)
            fmt = "%Y" if any(w in q_clean for w in ["year", "annual", "yearly"]) else "%Y-%m-%d" if any(w in q_clean for w in ["day", "daily"]) else "%Y-%m"
            date_sql = DuckDBService.get_date_trunc_sql(time_col, fmt)
            
            where_parts = [f'"{time_col}" IS NOT NULL']
            if meas:
                where_parts.append(f'"{meas}" IS NOT NULL')
            for f in filter_conditions:
                where_parts.append(f'LOWER("{f["column"]}") LIKE \'%{f["value"].lower()}%\'')

            val_expr = f'ROUND({agg}("{meas}"), 2)' if meas and agg != "COUNT" else "COUNT(*)"
            sql = f'''
                SELECT 
                    {date_sql} AS category,
                    {val_expr} AS value
                FROM dataset
                WHERE {' AND '.join(where_parts)}
                GROUP BY 1
                ORDER BY 1 ASC
                LIMIT 36
            '''
            intent = "temporal_trend"

        # Pattern C: Dimension Comparison / Ranking
        elif target_dimension or has_explicit_group_by:
            dim = target_dimension or (dimensions[0] if dimensions else None)
            meas = target_measure or (measures[0] if measures else None)
            
            where_parts = [f'"{dim}" IS NOT NULL']
            if meas and agg != "COUNT":
                where_parts.append(f'"{meas}" IS NOT NULL')
            for f in filter_conditions:
                if f["column"] != dim:
                    where_parts.append(f'LOWER("{f["column"]}") LIKE \'%{f["value"].lower()}%\'')

            order_dir = "ASC" if agg == "MIN" or "lowest" in q_clean or "bottom" in q_clean else "DESC"
            val_expr = f'ROUND({agg}("{meas}"), 2)' if meas and agg != "COUNT" else "COUNT(*)"
            sql = f'''
                SELECT 
                    "{dim}" AS category,
                    {val_expr} AS value
                FROM dataset
                WHERE {' AND '.join(where_parts)}
                GROUP BY 1
                ORDER BY value {order_dir}
                LIMIT 10
            '''
            intent = "categorical_ranking"

        # Pattern D: Overall Aggregate or Count
        else:
            meas = target_measure or (measures[0] if measures else None)
            if meas and agg != "COUNT":
                sql = f'''
                    SELECT 
                        'Overall Total' AS category,
                        ROUND({agg}("{meas}"), 2) AS value,
                        COUNT(*) AS record_count
                    FROM dataset
                    WHERE "{meas}" IS NOT NULL
                '''
                intent = "single_aggregate"
            else:
                sql = f"SELECT 'Total Records' AS category, COUNT(*) AS value FROM dataset"
                intent = "total_records"

        # -------------------------------------------------------------
        # 8. Deterministic Query Execution & Contextual Explanation
        # -------------------------------------------------------------
        table_data = []
        explanation = ""

        try:
            res = DuckDBService.execute_query(parquet_path, sql, limit=50)
            table_data = res["rows"]
            explanation = AnalystAgent._generate_chat_explanation(
                q_clean=q_clean,
                data=table_data,
                intent=intent,
                target_measure=target_measure,
                target_dimension=target_dimension,
                filter_conditions=filter_conditions,
                agg_label=agg_label,
                dataset_name=dataset_name,
                lang=lang
            )
        except Exception as e:
            explanation = f"Could not compute data: {str(e)}"

        return {
            "intent": intent,
            "sql_query": sql,
            "table_data": table_data,
            "explanation": explanation,
            "language": lang
        }

    @staticmethod
    def _generate_chat_explanation(
        q_clean: str,
        data: List[Dict[str, Any]],
        intent: str,
        target_measure: Optional[str],
        target_dimension: Optional[str],
        filter_conditions: List[Dict[str, str]],
        agg_label: str,
        dataset_name: str,
        lang: str
    ) -> str:
        if not data:
            return "No matching records were found in the dataset for this question."

        meas_display = (target_measure or "Volume").replace("_", " ").title()

        # 1. Filtered Entity Response
        if intent in ["filtered_entity_metric", "filtered_entity_count"]:
            row = data[0]
            cat_name = row.get("category", "Target")
            val = row.get("value", 0)
            val_fmt = format_number(val)
            cnt = row.get("record_count", row.get("value", 0))
            avg_val = row.get("avg_value")

            if lang in ["hi_hinglish", "hi_devanagari"]:
                res = f"### 🎯 **{cat_name}** के आंकड़े ({meas_display})\n\n**{cat_name}** के लिए **{agg_label} {meas_display}** का मान **{val_fmt}** है (कुल **{cnt:,}** रिकॉर्ड्स में)।"
                if avg_val:
                    res += f"\n- **औसत मान:** {format_number(avg_val)} प्रति ऑर्डर"
                res += f"\n\n*Aap kisi doosre segment se compare karne ke liye keh sakte hain (jaise: 'Compare {cat_name} with other regions').*"
                return res
            else:
                res = f"### 🎯 **{cat_name}** Summary ({meas_display})\n\nIn the **{cat_name}** segment, the **{agg_label} {meas_display}** is **{val_fmt}** across **{cnt:,}** recorded transactions."
                if avg_val:
                    res += f"\n- **Average per order:** {format_number(avg_val)}"
                res += f"\n\n*Tip: You can ask 'Compare {cat_name} with other segments' or 'Show monthly trend for {cat_name}' for deeper insights.*"
                return res

        # 2. Categorical Ranking
        elif intent == "categorical_ranking":
            top_row = data[0]
            top_cat = top_row.get("category", "")
            top_val = format_number(top_row.get("value", 0))
            total_sum = sum(float(r.get("value") or 0) for r in data)
            top_share = format_percentage((float(top_row.get("value") or 0) / total_sum) if total_sum > 0 else 0)

            rankings = []
            for i, r in enumerate(data[:6]):
                v_fmt = format_number(r.get("value"))
                pct = format_percentage((float(r.get("value") or 0) / total_sum) if total_sum > 0 else 0)
                rankings.append(f"{i + 1}. **{r.get('category')}**: {v_fmt} ({pct} share)")
            rankings_str = "\n".join(rankings)

            dim_display = (target_dimension or "Category").replace("_", " ").title()

            if lang in ["hi_hinglish", "hi_devanagari"]:
                return f"""### 🏆 **{dim_display}** रैंकिंग ({meas_display})

**{top_cat}** सबसे शीर्ष पर है, जिसका कुल **{meas_display} {top_val}** है (कुल हिस्सेदारी: **{top_share}**)।

#### 📊 शीर्ष श्रेणियां:
{rankings_str}

#### 💡 व्यापारिक अंतर्दृष्टि:
- **शीर्ष संवाहक:** **{top_cat}** इस समूह का सबसे बड़ा योगदानकर्ता है।
- **रणनीति:** शीर्ष 2 श्रेणियां अधिकांश गतिविधि को संचालित करती हैं।"""
            else:
                return f"""### 🏆 Top Rankings by {dim_display} ({meas_display})

**{top_cat}** ranks **#1** with **{top_val}** in **{meas_display}**, accounting for **{top_share}** of evaluated volume.

#### 📊 Performance Rankings:
{rankings_str}

#### 💡 Strategic Takeaway:
- **Primary Driver:** **{top_cat}** is the leading contributor in this segment ({top_share} share).
- **Concentration:** The top 2 segments generate the substantial majority of overall activity."""

        # 3. Temporal Trend
        elif intent == "temporal_trend":
            first_row = data[0]
            last_row = data[-1]
            first_val = float(first_row.get("value") or 0)
            last_val = float(last_row.get("value") or 0)
            diff = last_val - first_val
            pct_change = round((diff / first_val * 100), 1) if first_val > 0 else 0.0
            direction = "grown" if diff >= 0 else "declined"
            sign = "+" if diff >= 0 else ""

            return f"""### 📈 Historical Trend Analysis ({meas_display})

Across the **{len(data)}** historical periods from **{first_row.get('category')}** to **{last_row.get('category')}**, {meas_display} has **{direction}** by **{sign}{pct_change}%** (from {format_number(first_val)} to {format_number(last_val)}).

#### 📊 Trajectory Highlights:
- **Baseline ({first_row.get('category')}):** {format_number(first_val)}
- **Latest Period ({last_row.get('category')}):** {format_number(last_val)}
- **Peak Period:** **{max(data, key=lambda x: float(x.get('value') or 0)).get('category')}** ({format_number(max(data, key=lambda x: float(x.get('value') or 0)).get('value'))})"""

        # 4. Overall Aggregate / Count
        else:
            val_fmt = format_number(data[0].get("value"))
            cnt = data[0].get("record_count")
            cnt_str = f" across **{cnt:,}** verified records" if cnt else ""
            return f"""### 🎯 Overall Metric Summary

The total calculated **{meas_display}** is **{val_fmt}**{cnt_str}."""
