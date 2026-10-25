import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import duckdb
import numpy as np
import pandas as pd
from app.models.schemas import FilterCondition

FORBIDDEN_SQL_PATTERNS = [
    r"\bDROP\b", r"\bDELETE\b", r"\bINSERT\b", r"\bUPDATE\b", r"\bALTER\b",
    r"\bCREATE\b", r"\bTRUNCATE\b", r"\bEXEC\b", r"\bEXECUTE\b", r"\bATTACH\b",
    r"\bDETACH\b", r"\bCOPY\b\s+.*\s+\bTO\b", r"\bPRAGMA\b", r"\bINSTALL\b", r"\bLOAD\b"
]

class SQLEngine:
    @staticmethod
    def is_safe_query(sql: str) -> Tuple[bool, str]:
        """Validate that SQL is strictly read-only and free of destructive statements."""
        clean = sql.strip()
        if not clean.upper().startswith("SELECT") and not clean.upper().startswith("WITH"):
            return False, "Only SELECT or WITH analytical queries are permitted."

        for pattern in FORBIDDEN_SQL_PATTERNS:
            if re.search(pattern, clean, re.IGNORECASE):
                return False, f"Prohibited keyword detected: {pattern.strip('\\b')}"

        return True, ""

    @staticmethod
    def build_where_clause(filters: Optional[List[FilterCondition]]) -> str:
        """Construct a parameterized WHERE clause from filter conditions."""
        if not filters:
            return ""

        clauses = []
        for f in filters:
            col = f'"{f.column}"'
            op = f.operator.lower()
            val = f.value

            if op == "eq":
                if isinstance(val, (int, float)):
                    clauses.append(f"{col} = {val}")
                else:
                    str_val = str(val).replace("'", "''")
                    if re.match(r"^\d{4}$", str_val):
                        clauses.append(f"(CAST({col} AS VARCHAR) LIKE '{str_val}%' OR {col} = '{str_val}')")
                    else:
                        clauses.append(f"{col} = '{str_val}'")
            elif op == "like":
                clauses.append(f"CAST({col} AS VARCHAR) LIKE '{str(val).replace('\'', '\'\'')}'")
            elif op == "neq":
                if isinstance(val, (int, float)):
                    clauses.append(f"{col} != {val}")
                else:
                    clauses.append(f"{col} != '{str(val).replace('\'', '\'\'')}'")
            elif op in ["gt", ">"]:
                clauses.append(f"{col} > {float(val)}")
            elif op in ["gte", ">="]:
                clauses.append(f"{col} >= {float(val)}")
            elif op in ["lt", "<"]:
                clauses.append(f"{col} < {float(val)}")
            elif op in ["lte", "<="]:
                clauses.append(f"{col} <= {float(val)}")
            elif op == "in" and isinstance(val, list):
                if not val:
                    continue
                formatted = []
                for item in val:
                    if isinstance(item, (int, float)):
                        formatted.append(str(item))
                    else:
                        formatted.append(f"'{str(item).replace('\'', '\'\'')}'")
                clauses.append(f"{col} IN ({', '.join(formatted)})")
            elif op == "between" and isinstance(val, (list, tuple)) and len(val) == 2:
                clauses.append(f"{col} BETWEEN '{val[0]}' AND '{val[1]}'")

        return " WHERE " + " AND ".join(clauses) if clauses else ""

    @staticmethod
    def execute_query(parquet_path: Path, sql: str, limit: int = 1000) -> Dict[str, Any]:
        """
        Executes a validated analytical SQL query against the Parquet dataset using DuckDB.
        Replaces placeholder `data` or `dataset` with the actual parquet view.
        """
        parquet_path = Path(parquet_path)
        is_safe, err_msg = SQLEngine.is_safe_query(sql)
        if not is_safe:
            raise ValueError(f"SQL Security Violation: {err_msg}")

        con = duckdb.connect()
        try:
            view_path = str(parquet_path).replace("\\", "/")
            con.execute(f"CREATE VIEW dataset AS SELECT * FROM read_parquet('{view_path}')")
            con.execute("CREATE VIEW data AS SELECT * FROM dataset")

            # Check if query already has a LIMIT
            has_limit = bool(re.search(r"\bLIMIT\s+\d+", sql, re.IGNORECASE))
            run_sql = sql if has_limit else f"{sql.rstrip(';')} LIMIT {limit}"

            df = con.execute(run_sql).fetchdf()

            # Clean NaNs and Infinities for JSON serialization
            df = df.replace([np.inf, -np.inf], None)
            df = df.where(pd.notnull(df), None)

            # Convert datetime columns to strings
            for col in df.columns:
                if pd.api.types.is_datetime64_any_dtype(df[col]):
                    df[col] = df[col].dt.strftime("%Y-%m-%d %H:%M:%S")

            records = df.to_dict(orient="records")
            columns = list(df.columns)
            row_count = len(records)

            return {
                "columns": columns,
                "rows": records,
                "row_count": row_count,
                "query": run_sql
            }
        except Exception as e:
            raise RuntimeError(f"DuckDB Execution Error: {str(e)}")
        finally:
            con.close()

    @staticmethod
    def run_aggregate(
        parquet_path: Path,
        dimension: Optional[str] = None,
        measure: Optional[str] = None,
        aggregation: str = "sum",
        filters: Optional[List[FilterCondition]] = None,
        limit: int = 50,
        order_by_measure: bool = True
    ) -> List[Dict[str, Any]]:
        """Utility method to quickly aggregate data for charts & KPIs."""
        where_clause = SQLEngine.build_where_clause(filters)
        agg_func = aggregation.upper()
        if agg_func not in ["SUM", "AVG", "COUNT", "MIN", "MAX"]:
            agg_func = "SUM"

        if dimension and measure:
            sql = f'''
                SELECT 
                    "{dimension}" AS category, 
                    ROUND({agg_func}("{measure}"), 2) AS value
                FROM dataset
                {where_clause}
                WHERE "{dimension}" IS NOT NULL
                GROUP BY "{dimension}"
                ORDER BY {"value DESC" if order_by_measure else 'category ASC'}
                LIMIT {limit}
            '''
        elif dimension and not measure:
            sql = f'''
                SELECT 
                    "{dimension}" AS category, 
                    COUNT(*) AS value
                FROM dataset
                {where_clause}
                WHERE "{dimension}" IS NOT NULL
                GROUP BY "{dimension}"
                ORDER BY value DESC
                LIMIT {limit}
            '''
        elif measure and not dimension:
            sql = f'''
                SELECT 
                    ROUND({agg_func}("{measure}"), 2) AS value
                FROM dataset
                {where_clause}
            '''
        else:
            sql = f"SELECT COUNT(*) AS value FROM dataset {where_clause}"

        res = SQLEngine.execute_query(parquet_path, sql)
        return res["rows"]
