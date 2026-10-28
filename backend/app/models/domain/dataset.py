from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field

class ColumnMeta(BaseModel):
    name: str
    data_type: str  # 'int', 'float', 'string', 'datetime', 'boolean'
    semantic_type: str  # 'measure', 'dimension', 'time', 'identifier', 'target_candidate'
    nullable: bool = False
    null_count: int = 0
    null_percentage: float = 0.0
    unique_count: int = 0
    cardinality_ratio: float = 0.0
    sample_values: List[Any] = []
    min_val: Optional[Union[float, int, str]] = None
    max_val: Optional[Union[float, int, str]] = None
    mean_val: Optional[float] = None
    median_val: Optional[float] = None
    std_val: Optional[float] = None

class DataCleaningReport(BaseModel):
    original_rows: int
    cleaned_rows: int
    duplicates_removed: int
    missing_cells_imputed: int
    columns_imputed: List[str] = []
    data_health_score: float  # 0 to 100
    cleaning_actions: List[str] = []

class KPISpec(BaseModel):
    id: str
    title: str
    value: Union[float, int, str]
    formatted_value: str
    aggregation: str
    measure_column: str
    trend_direction: Optional[str] = "neutral"
    change_percentage: Optional[float] = None

class ChartSpec(BaseModel):
    id: str
    chart_type: str  # 'bar', 'line', 'area', 'pie', 'donut', 'scatter', 'treemap'
    title: str
    description: Optional[str] = ""
    x_axis: Optional[str] = None
    y_axis: Optional[str] = None
    aggregation: Optional[str] = "sum"
    data: List[Dict[str, Any]] = []
    insight: Optional[str] = None
    plotly_spec: Optional[Dict[str, Any]] = None
    echarts_option: Optional[Dict[str, Any]] = None

class DatasetProfile(BaseModel):
    dataset_id: str
    name: str
    filename: str
    file_format: str
    total_rows: int
    total_columns: int
    completeness: float
    duplicate_rows: int
    memory_usage_mb: float
    columns: List[ColumnMeta]
    primary_measures: List[str] = []
    primary_dimensions: List[str] = []
    primary_time_column: Optional[str] = None
    primary_id_column: Optional[str] = None
    cleaning_report: Optional[DataCleaningReport] = None
    created_at: str

class FilterCondition(BaseModel):
    column: str
    operator: str  # 'eq', 'neq', 'gt', 'gte', 'lt', 'lte', 'in', 'between', 'like'
    value: Any

class DashboardSpec(BaseModel):
    dataset_id: str
    title: str
    generated_at: str
    kpis: List[KPISpec]
    charts: List[ChartSpec]
    executive_summary: str
    applied_filters: Optional[List[FilterCondition]] = None
