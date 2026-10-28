import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import duckdb
import numpy as np
import pandas as pd
from app.core.errors import QuerySecurityError
from app.models.domain.dataset import FilterCondition

FORBIDDEN_SQL_PATTERNS = [
    r"\bDROP\b", r"\bDELETE\b", r"\bINSERT\b", r"\bUPDATE\b", r"\bALTER\b",
    r"\bCREATE\b", r"\bTRUNCATE\b", r"\bEXEC\b", r"\bEXECUTE\b", r"\bATTACH\b",
    r"\bDETACH\b", r"\bCOPY\b\s+.*\s+\bTO\b", r"\bPRAGMA\b", r"\bINSTALL\b", r"\bLOAD\b"
]

class DuckDBService:
    @staticmethod
    def validate_safety(sql: str) -> None:
        """Enforces strictly read-only SELECT / WITH analytical statements."""
        clean = sql.strip()
        if not clean.upper().startswith("SELECT") and not clean.upper().startswith("WITH"):
            raise QuerySecurityError("Only SELECT or WITH analytical statements are permitted.")

        for pattern in FORBIDDEN_SQL_PATTERNS:
            if re.search(pattern, clean, re.IGNORECASE):
                raise QuerySecurityError(f"Prohibited SQL operation detected: {pattern.strip('\\b')}")

    @staticmethod
    def get_date_trunc_sql(col_name: str, fmt: str = "%Y-%m") -> str:
        """
        Returns a resilient DuckDB SQL expression parsing varied date formats into strftime strings.
        Safely handles native TIMESTAMP, DATE, and diverse string date formats (ISO, DD/MM/YYYY, MM/DD/YYYY, etc.).
        """
        return (
            f"strftime("
            f"COALESCE("
            f"TRY_CAST(\"{col_name}\" AS TIMESTAMP), "
            f"TRY_CAST(\"{col_name}\" AS DATE), "
            f"TRY_STRPTIME(CAST(\"{col_name}\" AS VARCHAR), ["
            f"'%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%m-%d-%Y', "
            f"'%Y/%m/%d', '%d.%m.%Y', '%d-%b-%Y', '%d %b %Y', '%b %d, %Y', "
            f"'%B %d, %Y', '%Y-%m-%d %H:%M:%S', '%d/%m/%Y %H:%M:%S', '%m/%d/%Y %H:%M:%S'"
            f"])"
            f"), '{fmt}')"
        )

    @staticmethod
    def build_where_clause(filters: Optional[List[FilterCondition]]) -> str:
        """Constructs safe parameterized WHERE clauses supporting numeric, strings, and year filters."""
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
                clauses.append(f"{col} != '{str(val).replace('\'', '\'\'')}'")
            elif op in ["gt", ">"]:
                clauses.append(f"{col} > {float(val)}")
            elif op in ["gte", ">="]:
                clauses.append(f"{col} >= {float(val)}")
            elif op in ["lt", "<"]:
                clauses.append(f"{col} < {float(val)}")
            elif op in ["lte", "<="]:
                clauses.append(f"{col} <= {float(val)}")
            elif op == "in" and isinstance(val, list) and val:
                items = [f"'{str(v).replace('\'', '\'\'')}'" for v in val]
                clauses.append(f"{col} IN ({', '.join(items)})")
            elif op == "between" and isinstance(val, (list, tuple)) and len(val) == 2:
                clauses.append(f"{col} BETWEEN '{val[0]}' AND '{val[1]}'")

        return " WHERE " + " AND ".join(clauses) if clauses else ""

    @staticmethod
    def execute_query(parquet_path: Path, sql: str, limit: int = 1000) -> Dict[str, Any]:
        """Executes analytical SQL query against Parquet dataset view in DuckDB."""
        DuckDBService.validate_safety(sql)
        parquet_path = Path(parquet_path)
        if not parquet_path.exists():
            raise FileNotFoundError(f"Parquet file not found at {parquet_path}")

        con = duckdb.connect()
        try:
            view_path = str(parquet_path).replace("\\", "/")
            con.execute(f"CREATE VIEW dataset AS SELECT * FROM read_parquet('{view_path}')")
            con.execute("CREATE VIEW data AS SELECT * FROM dataset")

            has_limit = bool(re.search(r"\bLIMIT\s+\d+", sql, re.IGNORECASE))
            run_sql = sql if has_limit else f"{sql.rstrip(';')} LIMIT {limit}"

            df = con.execute(run_sql).fetchdf()
            df = df.replace([np.inf, -np.inf], None)
            df = df.where(pd.notnull(df), None)

            return {
                "columns": list(df.columns),
                "rows": df.to_dict(orient="records"),
                "row_count": len(df),
                "sql": run_sql
            }
        finally:
            con.close()
