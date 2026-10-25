import React from 'react';
import { Filter, X, RefreshCw } from 'lucide-react';
import { FilterCondition, DatasetProfile } from '../types';

interface FilterBarProps {
  profile: DatasetProfile | null;
  filters: FilterCondition[];
  onAddFilter: (column: string, value: string) => void;
  onRemoveFilter: (index: number) => void;
  onClearFilters: () => void;
  isFiltering: boolean;
}

export const FilterBar: React.FC<FilterBarProps> = ({
  profile,
  filters,
  onAddFilter,
  onRemoveFilter,
  onClearFilters,
  isFiltering
}) => {
  if (!profile) return null;

  const filterableDimensions = profile.columns.filter(
    c => c.semantic_type === 'dimension' && c.unique_count <= 25 && c.sample_values.length > 0
  );

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-3 shadow-md mb-6 backdrop-blur-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        
        {/* Left Side: Filter Dropdowns */}
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center text-xs font-semibold text-slate-400 mr-2">
            <Filter className="w-3.5 h-3.5 mr-1.5 text-indigo-400" />
            <span>Cross Filters:</span>
          </div>

          {filterableDimensions.slice(0, 4).map((dim) => (
            <div key={dim.name} className="relative">
              <select
                onChange={(e) => {
                  if (e.target.value) {
                    onAddFilter(dim.name, e.target.value);
                    e.target.value = '';
                  }
                }}
                defaultValue=""
                className="bg-slate-800/90 hover:bg-slate-800 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-300 focus:outline-none focus:ring-1 focus:ring-indigo-500 cursor-pointer"
              >
                <option value="" disabled>
                  Filter {dim.name.replace(/_/g, ' ')}...
                </option>
                {dim.sample_values.map((val) => (
                  <option key={val} value={val}>
                    {val}
                  </option>
                ))}
              </select>
            </div>
          ))}
        </div>

        {/* Right Side: Active Filter Badges */}
        <div className="flex flex-wrap items-center gap-2">
          {filters.map((f, idx) => (
            <span
              key={`${f.column}-${idx}`}
              className="inline-flex items-center space-x-1 bg-indigo-950/80 text-indigo-300 border border-indigo-700/60 px-2.5 py-1 rounded-md text-xs font-medium"
            >
              <span className="text-slate-400">{f.column}:</span>
              <span>{String(f.value)}</span>
              <button
                onClick={() => onRemoveFilter(idx)}
                className="hover:text-white p-0.5 rounded transition"
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}

          {filters.length > 0 && (
            <button
              onClick={onClearFilters}
              className="text-xs text-rose-400 hover:text-rose-300 font-medium px-2 py-1 rounded hover:bg-rose-950/40 transition flex items-center space-x-1"
            >
              <RefreshCw className={`w-3 h-3 ${isFiltering ? 'animate-spin' : ''}`} />
              <span>Reset Filters</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
