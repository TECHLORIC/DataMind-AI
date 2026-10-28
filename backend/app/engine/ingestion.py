import os
import uuid
import re
from pathlib import Path
from typing import Dict, Any, Tuple
import pandas as pd
import polars as pl
from app.config import UPLOAD_DIR, PARQUET_DIR

def sanitize_column_name(col: str) -> str:
    """Normalize and clean column name for SQL & Parquet compatibility."""
    c = str(col).strip()
    c = re.sub(r"[^\w\s]", "", c)
    c = re.sub(r"\s+", "_", c)
    if not c:
        c = "unnamed_column"
    return c

def deduplicate_columns(columns: list) -> list:
    """Ensure column names are unique."""
    seen = {}
    cleaned = []
    for col in columns:
        base = sanitize_column_name(col)
        if base in seen:
            seen[base] += 1
            cleaned.append(f"{base}_{seen[base]}")
        else:
            seen[base] = 0
            cleaned.append(base)
    return cleaned

class IngestionEngine:
    @staticmethod
    def process_file(file_path: Path, dataset_name: str = None) -> Dict[str, Any]:
        """
        Reads CSV, Excel, JSON, or Parquet, cleans column headers,
        and saves an optimized Parquet representation.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        dataset_id = f"ds_{uuid.uuid4().hex[:10]}"
        suffix = file_path.suffix.lower()
        original_name = dataset_name or file_path.stem
        file_size_mb = round(file_path.stat().st_size / (1024 * 1024), 3)

        # Ingest using pandas / polars depending on format
        try:
            if suffix in [".csv", ".txt"]:
                # Try UTF-8 first, fallback to latin-1
                try:
                    df = pd.read_csv(file_path, encoding="utf-8", low_memory=False)
                except UnicodeDecodeError:
                    df = pd.read_csv(file_path, encoding="latin-1", low_memory=False)
                fmt = "csv"
            elif suffix in [".xlsx", ".xls"]:
                df = pd.read_excel(file_path)
                fmt = "excel"
            elif suffix == ".json":
                df = pd.read_json(file_path)
                fmt = "json"
            elif suffix == ".parquet":
                df = pd.read_parquet(file_path)
                fmt = "parquet"
            else:
                raise ValueError(f"Unsupported file format: {suffix}. Supported formats: CSV, Excel, JSON, Parquet.")
        except Exception as e:
            raise RuntimeError(f"Failed to read file: {str(e)}")

        # Deduplicate & sanitize column headers
        df.columns = deduplicate_columns(df.columns)

        # Drop columns that are completely empty
        df = df.dropna(how="all", axis=1)

        # Convert object columns that look like datetimes
        for col in df.columns:
            if df[col].dtype == "object":
                # Check sample values
                sample = df[col].dropna().head(20)
                if len(sample) > 0 and any(keyword in col.lower() for keyword in ["date", "time", "year", "month", "timestamp"]):
                    try:
                        parsed = pd.to_datetime(df[col], format="mixed", errors="coerce")
                        if parsed.notnull().sum() / max(len(df[col]), 1) > 0.5:
                            df[col] = parsed
                    except Exception:
                        pass

        row_count = int(len(df))
        col_count = int(len(df.columns))

        # Save to Parquet
        parquet_filename = f"{dataset_id}.parquet"
        parquet_path = PARQUET_DIR / parquet_filename
        df.to_parquet(parquet_path, index=False, engine="pyarrow")

        return {
            "dataset_id": dataset_id,
            "name": original_name,
            "filename": file_path.name,
            "file_format": fmt,
            "file_size_mb": file_size_mb,
            "row_count": row_count,
            "col_count": col_count,
            "raw_path": str(file_path),
            "parquet_path": str(parquet_path),
        }
