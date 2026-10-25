import React, { useState } from 'react';
import {
  Database,
  Hash,
  Type,
  Calendar,
  Key,
  ChevronRight,
  ChevronLeft,
  Search,
  Filter,
  BarChart2,
  X
} from 'lucide-react';
import { DatasetProfile, ColumnMeta } from '../types';

interface PowerBIDataPaneProps {
  profile: DatasetProfile | null;
  isOpen: boolean;
  onToggle: () => void;
  onQuickFilter: (column: string, value: string) => void;
}

export const PowerBIDataPane: React.FC<PowerBIDataPaneProps> = ({
  profile,
  isOpen,
  onToggle,
  onQuickFilter
}) => {
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedColumn, setSelectedColumn] = useState<ColumnMeta | null>(null);

  if (!profile) return null;

  const filteredColumns = profile.columns.filter((c) =>
    c.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const measures = filteredColumns.filter((c) => c.semantic_type === 'measure');
  const dimensions = filteredColumns.filter((c) => c.semantic_type === 'dimension');
  const times = filteredColumns.filter((c) => c.semantic_type === 'time');
  const ids = filteredColumns.filter((c) => c.semantic_type === 'identifier');

  return (
    <>
      {/* Floating Toggle Tab Pill on right edge */}
      <button
        onClick={onToggle}
        className={`fixed top-24 right-0 z-30 flex items-center space-x-1.5 bg-slate-900 border-l border-y border-slate-700 text-slate-300 px-3 py-2 rounded-l-xl shadow-xl hover:bg-slate-800 transition ${
          isOpen ? 'translate-x-full opacity-0 pointer-events-none' : 'translate-x-0'
        }`}
      >
        <Database className="w-4 h-4 text-indigo-400" />
        <span className="text-xs font-semibold">Data Fields</span>
        <ChevronLeft className="w-3.5 h-3.5 text-slate-400" />
      </button>

      {/* Slide-out Power BI Fields Drawer */}
      <div
        className={`fixed inset-y-0 right-0 z-40 w-80 bg-slate-900/98 backdrop-blur-md border-l border-slate-800 shadow-2xl flex flex-col transition-transform duration-300 ease-in-out ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-800">
          <div className="flex items-center space-x-2">
            <Database className="w-4 h-4 text-indigo-400" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-white">
              Data Fields (Power BI)
            </h3>
          </div>
          <button
            onClick={onToggle}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>

        {/* Search Input */}
        <div className="p-3 border-b border-slate-800">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search attributes..."
              className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>
        </div>

        {/* Column Lists */}
        <div className="flex-1 overflow-y-auto p-3 space-y-4">
          {/* Measures Group (Sigma symbol) */}
          {measures.length > 0 && (
            <div>
              <div className="flex items-center space-x-1.5 text-[11px] font-bold uppercase tracking-wider text-emerald-400 mb-2">
                <span className="font-serif font-black text-sm">&Sigma;</span>
                <span>Measures ({measures.length})</span>
              </div>
              <div className="space-y-1">
                {measures.map((col) => (
                  <div
                    key={col.name}
                    onClick={() => setSelectedColumn(col)}
                    className="flex items-center justify-between p-2 rounded-lg bg-slate-800/40 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 cursor-pointer transition text-xs group"
                  >
                    <span className="font-medium text-slate-200 group-hover:text-emerald-300 truncate">
                      {col.name}
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono">
                      {col.mean_val !== null ? `μ ${col.mean_val}` : col.data_type}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Dimensions Group */}
          {dimensions.length > 0 && (
            <div>
              <div className="flex items-center space-x-1.5 text-[11px] font-bold uppercase tracking-wider text-indigo-400 mb-2">
                <Type className="w-3.5 h-3.5" />
                <span>Dimensions ({dimensions.length})</span>
              </div>
              <div className="space-y-1">
                {dimensions.map((col) => (
                  <div
                    key={col.name}
                    onClick={() => setSelectedColumn(col)}
                    className="flex items-center justify-between p-2 rounded-lg bg-slate-800/40 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 cursor-pointer transition text-xs group"
                  >
                    <span className="font-medium text-slate-200 group-hover:text-indigo-300 truncate">
                      {col.name}
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono">
                      {col.unique_count} unique
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Time Columns */}
          {times.length > 0 && (
            <div>
              <div className="flex items-center space-x-1.5 text-[11px] font-bold uppercase tracking-wider text-amber-400 mb-2">
                <Calendar className="w-3.5 h-3.5" />
                <span>Temporal / Dates ({times.length})</span>
              </div>
              <div className="space-y-1">
                {times.map((col) => (
                  <div
                    key={col.name}
                    onClick={() => setSelectedColumn(col)}
                    className="flex items-center justify-between p-2 rounded-lg bg-slate-800/40 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 cursor-pointer transition text-xs group"
                  >
                    <span className="font-medium text-slate-200 group-hover:text-amber-300 truncate">
                      {col.name}
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono">time</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Identifiers */}
          {ids.length > 0 && (
            <div>
              <div className="flex items-center space-x-1.5 text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-2">
                <Key className="w-3.5 h-3.5" />
                <span>Identifiers ({ids.length})</span>
              </div>
              <div className="space-y-1">
                {ids.map((col) => (
                  <div
                    key={col.name}
                    onClick={() => setSelectedColumn(col)}
                    className="flex items-center justify-between p-2 rounded-lg bg-slate-800/30 hover:bg-slate-800 border border-slate-800 cursor-pointer transition text-xs text-slate-400 group"
                  >
                    <span className="truncate">{col.name}</span>
                    <span className="text-[10px] font-mono text-slate-600">key</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Selected Field Quick Inspector Drawer Modal */}
        {selectedColumn && (
          <div className="p-4 border-t border-slate-800 bg-slate-950/80">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-white truncate">{selectedColumn.name}</span>
              <button
                onClick={() => setSelectedColumn(null)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="text-[11px] text-slate-400 space-y-1 mb-3">
              <div>Type: <span className="font-mono text-slate-200">{selectedColumn.data_type}</span></div>
              <div>Unique: <span className="font-mono text-slate-200">{selectedColumn.unique_count}</span></div>
              {selectedColumn.mean_val !== null && selectedColumn.mean_val !== undefined && (
                <div>Mean: <span className="font-mono text-slate-200">{selectedColumn.mean_val}</span> (min: {selectedColumn.min_val}, max: {selectedColumn.max_val})</div>
              )}
            </div>

            {selectedColumn.sample_values.length > 0 && (
              <div>
                <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider block mb-1">
                  Sample Values (Click to Filter):
                </span>
                <div className="flex flex-wrap gap-1 max-h-24 overflow-y-auto">
                  {selectedColumn.sample_values.map((v) => (
                    <button
                      key={v}
                      onClick={() => onQuickFilter(selectedColumn.name, v)}
                      className="text-[10px] bg-slate-800 hover:bg-indigo-600 hover:text-white text-slate-300 px-2 py-0.5 rounded transition"
                    >
                      {v}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </>
  );
};
