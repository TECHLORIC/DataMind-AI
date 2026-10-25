export interface ColumnMeta {
  name: string;
  data_type: string;
  semantic_type: 'measure' | 'dimension' | 'time' | 'identifier' | 'target_candidate';
  nullable: boolean;
  null_count: number;
  null_percentage: number;
  unique_count: number;
  cardinality_ratio: number;
  sample_values: string[];
  min_val?: number | string | null;
  max_val?: number | string | null;
  mean_val?: number | null;
  median_val?: number | null;
  std_val?: number | null;
}

export interface DatasetProfile {
  dataset_id: string;
  name: string;
  filename: string;
  file_format: string;
  total_rows: number;
  total_columns: number;
  completeness: number;
  duplicate_rows: number;
  memory_usage_mb: number;
  columns: ColumnMeta[];
  primary_measures: string[];
  primary_dimensions: string[];
  primary_time_column?: string | null;
  primary_id_column?: string | null;
  created_at: string;
}

export interface KPICard {
  id: string;
  title: string;
  value: number | string;
  formatted_value: string;
  aggregation: string;
  measure_column: string;
  change_percentage?: number | null;
  trend_direction?: 'up' | 'down' | 'neutral' | null;
}

export interface ChartSpec {
  id: string;
  chart_type: 'bar' | 'line' | 'area' | 'pie' | 'donut' | 'scatter' | 'histogram' | 'table';
  title: string;
  description?: string;
  x_axis?: string;
  y_axis?: string;
  group_by?: string;
  aggregation?: string;
  data: any[];
  insight?: string;
  echarts_option?: any;
}

export interface FilterCondition {
  column: string;
  operator: string;
  value: any;
}

export interface DashboardSpec {
  dataset_id: string;
  title: string;
  generated_at: string;
  kpis: KPICard[];
  charts: ChartSpec[];
  executive_summary: string;
  applied_filters?: FilterCondition[];
}

export interface DatasetItem {
  id: string;
  name: string;
  filename: string;
  file_format: string;
  file_size_mb: number;
  row_count: number;
  col_count: number;
  created_at?: string;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  sql_query?: string | null;
  table_data?: any[] | null;
  chart?: ChartSpec | null;
  confidence?: number;
  timestamp: string;
}

export interface InsightItem {
  id: string;
  category: 'trend' | 'anomaly' | 'correlation' | 'segmentation' | 'distribution';
  importance: 'high' | 'medium' | 'info';
  title: string;
  description: string;
  metric?: string;
  score?: number;
  evidence: Record<string, any>;
  chart?: ChartSpec;
}

export interface InsightsResponse {
  dataset_id: string;
  generated_at: string;
  total_insights: number;
  insights: InsightItem[];
  executive_takeaways: string[];
}

export interface MLTrainResponse {
  model_id: string;
  dataset_id: string;
  task_type: string;
  target_column?: string;
  features_used: string[];
  algorithm_name: string;
  metrics: Record<string, any>;
  feature_importance: { feature: string; importance: number; percentage?: number }[];
  model_leaderboard?: { algorithm: string; primary_metric: string; score: number; is_best: boolean }[];
  target_distribution?: { type: string; labels: string[]; values: number[] } | null;
  actual_vs_predicted?: { actual: number; predicted: number }[] | null;
  residuals?: { sample: number; error: number }[] | null;
  confusion_matrix?: { classes: string[]; matrix: number[][] } | null;
  forecast_data?: { period: string; actual?: number | null; forecast?: number | null; lower_bound?: number | null; upper_bound?: number | null }[];
  cluster_centers?: any[];
  feature_meta?: Record<string, any>;
  created_at: string;
  summary: string;
}

export interface MLPredictResponse {
  model_id: string;
  prediction: number | string;
  probabilities?: Record<string, number>;
  confidence?: number;
  explanation: string;
}
