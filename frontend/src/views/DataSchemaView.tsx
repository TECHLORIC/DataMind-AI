import React, { useState } from 'react';
import {
  Database,
  Code2,
  Play,
  FileSpreadsheet,
  CheckCircle2,
  AlertCircle,
  HardDrive,
  Layers,
  Loader2
} from 'lucide-react';
import axios from 'axios';
import { DatasetProfile } from '../types';

interface DataSchemaViewProps {
  datasetId: string;
  profile: DatasetProfile | null;
}

export const DataSchemaView: React.FC<DataSchemaViewProps> = ({
  datasetId,
  profile
}) => {
  const [customSQL, setCustomSQL] = useState<string>('SELECT * FROM dataset LIMIT 20');
  const [queryResult, setQueryResult] = useState<any | null>(null);
  const [isQuerying, setIsQuerying] = useState<boolean>(false);
  const [queryError, setQueryError] = useState<string | null>(null);

  if (!profile) return null;

  const handleRunSQL = async () => {
    setIsQuerying(true);
    setQueryError(null);

    try {
      const res = await axios.post(`/api/v1/datasets/${datasetId}/query`, {
        dataset_id: datasetId,
        sql: customSQL
      });
      setQueryResult(res.data);
      setIsQuerying(false);
    } catch (err: any) {
      setIsQuerying(false);
      setQueryError(err.response?.data?.detail || 'Query execution failed.');
    }
  };

  const getSemanticColor = (semantic: string) => {
    switch (semantic) {
      case 'measure':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      case 'dimension':
        return 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30';
      case 'time':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      case 'identifier':
        return 'bg-slate-700 text-slate-300 border-slate-600';
      default:
        return 'bg-slate-800 text-slate-400 border-slate-700';
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-8">
      
      {/* Header & Quality Score */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-xl font-bold text-white tracking-tight">
              Dynamic Schema & Data Profiling
            </h1>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 font-medium">
              {profile.file_format.toUpperCase()}
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Zero-hardcoding dynamic schema discovery, cardinality profiling, and semantic classification.
          </p>
        </div>

        {/* Completeness Health Badge */}
        <div className="flex items-center space-x-3 bg-slate-900 border border-slate-800 p-3 rounded-xl">
          <div className="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center justify-center font-bold text-xs">
            {profile.completeness}%
          </div>
          <div>
            <span className="text-xs font-semibold text-white block">Data Completeness</span>
            <span className="text-[11px] text-slate-400">
              {profile.duplicate_rows === 0 ? 'No duplicate rows detected' : `${profile.duplicate_rows} duplicate rows`}
            </span>
          </div>
        </div>
      </div>

      {/* Overview Metric Badges */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl">
          <span className="text-[10px] font-bold uppercase text-slate-500 tracking-wider block mb-1">
            Total Records
          </span>
          <span className="text-2xl font-black text-white">{profile.total_rows.toLocaleString()}</span>
        </div>
        <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl">
          <span className="text-[10px] font-bold uppercase text-slate-500 tracking-wider block mb-1">
            Columns / Attributes
          </span>
          <span className="text-2xl font-black text-white">{profile.total_columns}</span>
        </div>
        <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl">
          <span className="text-[10px] font-bold uppercase text-slate-500 tracking-wider block mb-1">
            Memory Footprint
          </span>
          <span className="text-2xl font-black text-white">{profile.memory_usage_mb} MB</span>
        </div>
        <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl">
          <span className="text-[10px] font-bold uppercase text-slate-500 tracking-wider block mb-1">
            Primary Time Dimension
          </span>
          <span className="text-base font-bold text-indigo-300 truncate block">
            {profile.primary_time_column || 'None Detected'}
          </span>
        </div>
      </div>

      {/* Dynamic Columns Schema Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl">
        <h2 className="text-sm font-semibold text-white mb-4 flex items-center space-x-2">
          <Database className="w-4 h-4 text-indigo-400" />
          <span>Attribute Schema & Semantic Classification</span>
        </h2>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-800/80 text-slate-400 uppercase text-[10px] border-b border-slate-700">
              <tr>
                <th className="px-4 py-3 font-semibold">Column Name</th>
                <th className="px-4 py-3 font-semibold">Data Type</th>
                <th className="px-4 py-3 font-semibold">Semantic Role</th>
                <th className="px-4 py-3 font-semibold">Unique Values</th>
                <th className="px-4 py-3 font-semibold">Missing (Null)</th>
                <th className="px-4 py-3 font-semibold">Summary Stats</th>
                <th className="px-4 py-3 font-semibold">Sample Values</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
              {profile.columns.map((col) => (
                <tr key={col.name} className="hover:bg-slate-800/30 transition">
                  <td className="px-4 py-3 font-semibold text-white">{col.name}</td>
                  <td className="px-4 py-3 text-slate-400">{col.data_type}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full border ${getSemanticColor(
                        col.semantic_type
                      )}`}
                    >
                      {col.semantic_type}
                    </span>
                  </td>
                  <td className="px-4 py-3">{col.unique_count.toLocaleString()}</td>
                  <td className="px-4 py-3">
                    {col.null_count > 0 ? (
                      <span className="text-amber-400">
                        {col.null_count} ({col.null_percentage}%)
                      </span>
                    ) : (
                      <span className="text-emerald-400">0%</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-slate-400">
                    {col.mean_val !== null && col.mean_val !== undefined ? (
                      <span>
                        μ: {col.mean_val} | min: {col.min_val} | max: {col.max_val}
                      </span>
                    ) : (
                      <span className="text-slate-600">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-slate-400 truncate max-w-xs font-sans text-xs">
                    {col.sample_values.slice(0, 3).join(', ')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Live DuckDB SQL Query Console */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <Code2 className="w-4 h-4 text-indigo-400" />
            <h2 className="text-sm font-semibold text-white">Live Analytical DuckDB SQL Console</h2>
          </div>
          <button
            onClick={handleRunSQL}
            disabled={isQuerying}
            className="flex items-center space-x-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold px-4 py-2 rounded-lg transition shadow-md shadow-indigo-600/30"
          >
            {isQuerying ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Play className="w-3.5 h-3.5" />
            )}
            <span>Execute Query</span>
          </button>
        </div>

        <textarea
          value={customSQL}
          onChange={(e) => setCustomSQL(e.target.value)}
          rows={3}
          className="w-full bg-slate-950 font-mono text-xs text-indigo-200 border border-slate-800 rounded-xl p-3 focus:outline-none focus:ring-1 focus:ring-indigo-500 mb-4"
        />

        {queryError && (
          <div className="p-3 mb-4 rounded-lg bg-rose-950/40 border border-rose-800 text-xs text-rose-300">
            {queryError}
          </div>
        )}

        {/* SQL Output Table */}
        {queryResult && (
          <div className="border border-slate-800 rounded-xl overflow-hidden">
            <div className="bg-slate-800/60 px-4 py-2 text-xs font-medium text-slate-400 border-b border-slate-700 flex justify-between">
              <span>Output: {queryResult.row_count} rows</span>
              <span className="font-mono text-[10px] text-slate-500">Query Verified</span>
            </div>
            <div className="max-h-72 overflow-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-800/80 text-slate-400 uppercase text-[10px] sticky top-0">
                  <tr>
                    {queryResult.columns.map((c: string) => (
                      <th key={c} className="px-3 py-2 font-medium">
                        {c}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 font-mono text-[11px]">
                  {queryResult.rows.map((row: any, i: number) => (
                    <tr key={i} className="hover:bg-slate-800/40">
                      {queryResult.columns.map((c: string) => (
                        <td key={c} className="px-3 py-2 truncate max-w-[150px]">
                          {typeof row[c] === 'number' ? row[c].toLocaleString() : String(row[c])}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
