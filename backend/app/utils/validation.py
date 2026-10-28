import re
import csv
from pathlib import Path
from typing import Tuple, List, Optional
import pandas as pd
from app.core.errors import CorruptedDataError, EncodingDetectionError, UnsupportedFormatError

COMMON_ENCODINGS = ["utf-8", "utf-8-sig", "latin1", "cp1252", "iso-8859-1"]

def detect_file_encoding(file_path: Path) -> str:
    """Attempts to read header bytes with common encodings to find a valid match."""
    with open(file_path, "rb") as f:
        sample = f.read(16384)
    if not sample:
        raise CorruptedDataError("Uploaded file is empty (0 bytes).")
    
    for enc in COMMON_ENCODINGS:
        try:
            sample.decode(enc)
            return enc
        except UnicodeDecodeError:
            continue
            
    raise EncodingDetectionError(
        "Unable to detect file encoding. Please ensure the file is saved in standard UTF-8."
    )

def detect_csv_delimiter(file_path: Path, encoding: str) -> str:
    """Uses csv.Sniffer to identify CSV delimiter (defaulting to comma)."""
    try:
        with open(file_path, "r", encoding=encoding, errors="replace") as f:
            sample = f.read(8192)
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(sample, delimiters=[",", "\t", ";", "|"])
            return dialect.delimiter
    except Exception:
        return ","

def sanitize_column_name(col: str, index: int) -> str:
    """Normalizes column names to clean alphanumeric strings without illegal characters."""
    c = str(col).strip()
    if not c or c.lower() in ["unnamed", "none", "nan", "null"]:
        return f"column_{index + 1}"
    c = re.sub(r"[^\w\s-]", "", c)
    c = re.sub(r"\s+", "_", c)
    return c[:64]

def sanitize_dataframe_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Deduplicates and cleans all column names in a DataFrame."""
    seen = {}
    new_cols = []
    for i, col in enumerate(df.columns):
        clean = sanitize_column_name(str(col), i)
        if clean in seen:
            seen[clean] += 1
            clean = f"{clean}_{seen[clean]}"
        else:
            seen[clean] = 0
        new_cols.append(clean)
    df.columns = new_cols
    return df

def validate_and_load_file(file_path: Path, original_filename: str) -> pd.DataFrame:
    """
    Robust reader for CSV and Excel files with encoding detection,
    delimiter sniffing, corrupted byte recovery, and column sanitization.
    """
    ext = file_path.suffix.lower()
    
    if ext not in [".csv", ".tsv", ".txt", ".xlsx", ".xls"]:
        raise UnsupportedFormatError(
            f"File format '{ext}' is not supported. Please upload CSV or Excel files."
        )

    try:
        if ext in [".xlsx", ".xls"]:
            # Load first sheet with openpyxl
            df = pd.read_excel(file_path, engine="openpyxl" if ext == ".xlsx" else None)
        else:
            encoding = detect_file_encoding(file_path)
            delimiter = detect_csv_delimiter(file_path, encoding)
            df = pd.read_csv(
                file_path,
                encoding=encoding,
                sep=delimiter,
                on_bad_lines="skip",
                low_memory=False
            )
    except Exception as e:
        raise CorruptedDataError(
            f"Failed to parse '{original_filename}': {str(e)}",
            details={"original_filename": original_filename, "error": str(e)}
        )

    if df.empty:
        raise CorruptedDataError("The dataset contains zero rows of data.")
        
    if len(df.columns) == 0:
        raise CorruptedDataError("The dataset has no identifiable columns.")

    df = sanitize_dataframe_columns(df)
    return df
