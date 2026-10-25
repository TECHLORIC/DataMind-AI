import React from 'react';
import {
  FileText,
  BarChart,
  Sparkles,
  Download,
  Filter,
  Share2
} from 'lucide-react';
import { DashboardSpec, DatasetProfile, FilterCondition } from '../types';
import { KPICardGrid } from '../components/KPICardGrid';
import { ChartCard } from '../components/ChartCard';
import { FilterBar } from '../components/FilterBar';

interface DashboardViewProps {
  dashboard: DashboardSpec | null;
  profile: DatasetProfile | null;
  filters: FilterCondition[];
  onAddFilter: (col: string, val: string) => void;
  onRemoveFilter: (idx: number) => void;
  onClearFilters: () => void;
  isFiltering: boolean;
  onOpenReportModal: () => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  dashboard,
  profile,
  filters,
  onAddFilter,
  onRemoveFilter,
  onClearFilters,
  isFiltering,
  onOpenReportModal
}) => {
  if (!dashboard) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] text-slate-400">
        <BarChart className="w-12 h-12 text-slate-600 mb-3 animate-pulse" />
        <p className="text-sm">No dataset loaded. Upload or select a dataset above.</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 animate-fadeIn">
      
      {/* Top Section: Dashboard Title & Executive Summary */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-xl font-bold text-white tracking-tight">
              {dashboard.title}
            </h1>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
              Live BI Engine
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1 max-w-3xl leading-relaxed">
            {dashboard.executive_summary}
          </p>
        </div>

        {/* Export / Actions */}
        <div className="flex items-center space-x-2">
          <button
            onClick={onOpenReportModal}
            className="flex items-center space-x-1.5 bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white text-xs font-semibold px-4 py-2 rounded-xl shadow-md shadow-indigo-600/30 transition active:scale-95"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download PDF Report</span>
          </button>
        </div>
      </div>

      {/* Dynamic Cross Filter Bar */}
      <FilterBar
        profile={profile}
        filters={filters}
        onAddFilter={onAddFilter}
        onRemoveFilter={onRemoveFilter}
        onClearFilters={onClearFilters}
        isFiltering={isFiltering}
      />

      {/* KPI Cards Grid */}
      <KPICardGrid kpis={dashboard.kpis} />

      {/* Dynamic Visualizations Grid with Click-To-Filter */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {dashboard.charts.map((chart) => (
          <ChartCard
            key={chart.id}
            chart={chart}
            onCrossFilter={(col, val) => onAddFilter(col, val)}
          />
        ))}
      </div>
    </div>
  );
};
