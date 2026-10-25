import React from 'react';
import { TrendingUp, TrendingDown, Minus, Hash, Activity } from 'lucide-react';
import { KPICard } from '../types';

interface KPICardGridProps {
  kpis: KPICard[];
}

export const KPICardGrid: React.FC<KPICardGridProps> = ({ kpis }) => {
  if (!kpis || kpis.length === 0) return null;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {kpis.map((kpi) => {
        const isUp = kpi.trend_direction === 'up';
        const isDown = kpi.trend_direction === 'down';

        return (
          <div
            key={kpi.id}
            className="relative overflow-hidden bg-slate-900/80 border border-slate-800 hover:border-slate-700/80 rounded-xl p-4 transition-all duration-200 hover:shadow-lg hover:shadow-indigo-500/5 group"
          >
            {/* Top Row: Title & Aggregation Pill */}
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-slate-400 truncate pr-2">
                {kpi.title}
              </span>
              <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                {kpi.aggregation}
              </span>
            </div>

            {/* Middle: Big Formatted Value */}
            <div className="flex items-baseline space-x-2 my-1">
              <span className="text-2xl font-extrabold tracking-tight text-white group-hover:text-indigo-200 transition">
                {kpi.formatted_value}
              </span>
            </div>

            {/* Bottom Row: Context / Trend Indicator */}
            <div className="flex items-center justify-between text-xs pt-2 border-t border-slate-800/60 text-slate-500">
              <span className="text-[11px] truncate">Column: {kpi.measure_column}</span>
              <div className="flex items-center space-x-1">
                {isUp ? (
                  <span className="flex items-center text-emerald-400 font-medium text-[11px]">
                    <TrendingUp className="w-3 h-3 mr-0.5" />
                    Active
                  </span>
                ) : isDown ? (
                  <span className="flex items-center text-rose-400 font-medium text-[11px]">
                    <TrendingDown className="w-3 h-3 mr-0.5" />
                    Drop
                  </span>
                ) : (
                  <span className="flex items-center text-slate-400 text-[11px]">
                    <Minus className="w-3 h-3 mr-0.5" />
                    Base
                  </span>
                )}
              </div>
            </div>

            {/* Subtle Gradient Glow */}
            <div className="absolute top-0 right-0 w-24 h-24 bg-indigo-500/5 rounded-full blur-2xl pointer-events-none group-hover:bg-indigo-500/10 transition" />
          </div>
        );
      })}
    </div>
  );
};
