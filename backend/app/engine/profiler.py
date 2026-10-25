import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import duckdb
import numpy as np
import pandas as pd
from app.models.schemas import ColumnMeta, DatasetProfile

class ProfilerEngine:
    @staticmethod
    def profile_parquet(parquet_path: Path, dataset_id: str, name: str, filename: str, file_format: str) -> DatasetProfile:
        """
        Profiles the dataset dynamically using DuckDB and Polars/Pandas.
        Detects semantic types, missing values, duplicates, and statistical metrics.
        """
        parquet_path = Path(parquet_path)
        con = duckdb.connect()

        # Load Parquet into DuckDB view
        con.execute(f"CREATE VIEW ds_view AS SELECT * FROM read_parquet('{str(parquet_path).replace('\\', '/')}')")

        # Basic metadata
        total_rows = con.execute("SELECT COUNT(*) FROM ds_view").fetchone()[0]
        schema_info = con.execute("DESCRIBE ds_view").fetchall()
        # schema_info: [(column_name, column_type, null, key, default, extra), ...]

        # Check duplicate rows (sample if huge dataset)
        duplicate_rows = 0
        if total_rows > 0:
            try:
                unique_rows = con.execute("SELECT COUNT(*) FROM (SELECT DISTINCT * FROM ds_view)").fetchone()[0]
                duplicate_rows = max(0, total_rows - unique_rows)
            except Exception:
                duplicate_rows = 0

        # Memory usage
        memory_mb = round(parquet_path.stat().st_size / (1024 * 1024), 3)

        # Profile columns
        columns_meta: List[ColumnMeta] = []
        primary_measures: List[str] = []
        primary_dimensions: List[str] = []
        primary_time_col: Optional[str] = None
        primary_id_col: Optional[str] = None

        total_null_cells = 0
        total_cells = total_rows * len(schema_info) if total_rows > 0 else 1

        for col_name, col_type, *rest in schema_info:
            col_type_lower = col_type.lower()

            # Null count & Unique count
            null_count = con.execute(f'SELECT COUNT(*) FROM ds_view WHERE "{col_name}" IS NULL').fetchone()[0]
            total_null_cells += null_count
            null_pct = round((null_count / total_rows * 100), 2) if total_rows > 0 else 0.0

            try:
                unique_count = con.execute(f'SELECT COUNT(DISTINCT "{col_name}") FROM ds_view WHERE "{col_name}" IS NOT NULL').fetchone()[0]
            except Exception:
                unique_count = 0
            
            cardinality_ratio = round(unique_count / total_rows, 4) if total_rows > 0 else 0.0

            # Sample values (up to 5)
            try:
                sample_rows = con.execute(f'SELECT DISTINCT "{col_name}" FROM ds_view WHERE "{col_name}" IS NOT NULL LIMIT 5').fetchall()
                sample_values = [r[0] for r in sample_rows]
            except Exception:
                sample_values = []

            # Determine simplified data type
            if any(t in col_type_lower for t in ["int", "bigint", "smallint", "tinyint", "hugeint"]):
                sim_type = "int"
            elif any(t in col_type_lower for t in ["float", "double", "decimal", "numeric", "real"]):
                sim_type = "float"
            elif any(t in col_type_lower for t in ["date", "time", "timestamp"]):
                sim_type = "datetime"
            elif "bool" in col_type_lower:
                sim_type = "boolean"
            else:
                sim_type = "string"

            # Compute stats for numeric columns
            min_val = None
            max_val = None
            mean_val = None
            median_val = None
            std_val = None

            if sim_type in ["int", "float"] and total_rows > 0:
                try:
                    stats = con.execute(f'''
                        SELECT 
                            MIN("{col_name}"), 
                            MAX("{col_name}"), 
                            AVG("{col_name}"), 
                            MEDIAN("{col_name}"), 
                            STDDEV_SAMP("{col_name}") 
                        FROM ds_view WHERE "{col_name}" IS NOT NULL
                    ''').fetchone()
                    if stats:
                        min_val = round(float(stats[0]), 2) if stats[0] is not None else None
                        max_val = round(float(stats[1]), 2) if stats[1] is not None else None
                        mean_val = round(float(stats[2]), 2) if stats[2] is not None else None
                        median_val = round(float(stats[3]), 2) if stats[3] is not None else None
                        std_val = round(float(stats[4]), 2) if stats[4] is not None else None
                except Exception:
                    pass

            # Determine Semantic Type
            semantic_type = "dimension"
            lower_name = col_name.lower()

            # Rule 1: Date/Time
            if sim_type == "datetime" or any(k in lower_name for k in ["date", "time", "year", "month", "timestamp", "quarter"]):
                semantic_type = "time"
                if not primary_time_col:
                    primary_time_col = col_name

            # Rule 2: Identifier
            elif (
                (lower_name.endswith("_id") or lower_name.startswith("id_") or lower_name == "id" or "code" in lower_name or "guid" in lower_name or "uuid" in lower_name)
                and cardinality_ratio > 0.6
            ) or (cardinality_ratio >= 0.98 and total_rows > 20):
                semantic_type = "identifier"
                if not primary_id_col:
                    primary_id_col = col_name

            # Rule 3: Measure (Continuous numeric attribute)
            elif sim_type in ["float", "int"]:
                # If integer has very few unique values (e.g. 1 to 5), it could be a category/rating/score or dimension
                if sim_type == "int" and unique_count <= 6 and not any(k in lower_name for k in ["amount", "revenue", "sales", "price", "profit", "cost", "quantity", "marks", "score"]):
                    semantic_type = "dimension"
                else:
                    semantic_type = "measure"
                    primary_measures.append(col_name)

            # Rule 4: Dimension (Categorical / Low cardinality)
            else:
                semantic_type = "dimension"
                # Good dimensions have between 2 and 50 unique values
                if 2 <= unique_count <= 100:
                    primary_dimensions.append(col_name)

            col_meta = ColumnMeta(
                name=col_name,
                data_type=sim_type,
                semantic_type=semantic_type,
                nullable=(null_count > 0),
                null_count=null_count,
                null_percentage=null_pct,
                unique_count=unique_count,
                cardinality_ratio=cardinality_ratio,
                sample_values=[str(v) for v in sample_values],
                min_val=min_val,
                max_val=max_val,
                mean_val=mean_val,
                median_val=median_val,
                std_val=std_val
            )
            columns_meta.append(col_meta)

        # Calculate overall completeness
        completeness = round(((total_cells - total_null_cells) / total_cells * 100), 2) if total_cells > 0 else 100.0

        con.close()

        return DatasetProfile(
            dataset_id=dataset_id,
            name=name,
            filename=filename,
            file_format=file_format,
            total_rows=total_rows,
            total_columns=len(columns_meta),
            completeness=completeness,
            duplicate_rows=duplicate_rows,
            memory_usage_mb=memory_mb,
            columns=columns_meta,
            primary_measures=primary_measures[:10],
            primary_dimensions=primary_dimensions[:10],
            primary_time_column=primary_time_col,
            primary_id_column=primary_id_col,
            created_at=datetime.datetime.utcnow().isoformat()
        )
