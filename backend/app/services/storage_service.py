import uuid
from pathlib import Path
from typing import Tuple
import pandas as pd
from app.core.config import UPLOAD_DIR, PARQUET_DIR

class StorageService:
    @staticmethod
    def generate_dataset_id() -> str:
        return f"ds_{uuid.uuid4().hex[:10]}"

    @staticmethod
    def save_raw_upload(filename: str, content: bytes) -> Tuple[str, Path]:
        dataset_id = StorageService.generate_dataset_id()
        suffix = Path(filename).suffix.lower()
        target_path = UPLOAD_DIR / f"{dataset_id}{suffix}"
        with open(target_path, "wb") as f:
            f.write(content)
        return dataset_id, target_path

    @staticmethod
    def save_clean_parquet(dataset_id: str, df: pd.DataFrame) -> Path:
        target_path = PARQUET_DIR / f"{dataset_id}.parquet"
        df.to_parquet(target_path, engine="pyarrow", compression="snappy", index=False)
        return target_path

    @staticmethod
    def get_parquet_path(dataset_id: str) -> Path:
        return PARQUET_DIR / f"{dataset_id}.parquet"
