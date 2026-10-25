import React from 'react';
import {
  Sparkles,
  TrendingUp,
  AlertTriangle,
  GitCommit,
  PieChart,
  Lightbulb,
  CheckCircle2
} from 'lucide-react';
import { InsightsResponse } from '../types';

interface InsightsViewProps {
  insightsData: InsightsResponse | null;
  onRefresh: () => void;
  isLoading: boolean;
}

export const InsightsView: React.FC<InsightsViewProps> = ({
  insightsData,
  onRefresh,
  isLoading
}) => {
  if (!insightsData || insightsData.insights.length === 0) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-12 text-center text-slate-400">
        <Sparkles className="w-10 h-10 text-indigo-400 mx-auto mb-3" />
        <h3 className="text-sm font-semibold text-white">No Insights Generated Yet</h3>
        <p className="text-xs text-slate-500 mt-1 mb-4">
          Click below to run automated pattern, correlation, and anomaly discovery.
        </p>
        <button
          onClick={onRefresh}
          className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs px-4 py-2 rounded-lg font-medium shadow-md shadow-indigo-600/30"
        >
          Generate AI Insights
        </button>
      </div>
    );
  }

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'correlation':
        return <GitCommit className="w-4 h-4 text-cyan-400" />;
      case 'anomaly':
        return <AlertTriangle className="w-4 h-4 text-rose-400" />;
      case 'trend':
        return <TrendingUp className="w-4 h-4 text-emerald-400" />;
      case 'segmentation':
        return <PieChart className="w-4 h-4 text-amber-400" />;
      default:
        return <Lightbulb className="w-4 h-4 text-indigo-400" />;
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-xl font-bold text-white tracking-tight">
              AI Insights & Automated Analysis
            </h1>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 font-medium">
              {insightsData.total_insights} Discoveries
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Autonomous statistical evaluation discovering trends, multi-variable correlations, and distribution anomalies.
          </p>
        </div>

        <button
          onClick={onRefresh}
          disabled={isLoading}
          className="flex items-center space-x-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium px-3.5 py-2 rounded-lg border border-slate-700 transition"
        >
          <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
          <span>Re-analyze</span>
        </button>
      </div>

      {/* Executive Takeaways Box */}
      {insightsData.executive_takeaways.length > 0 && (
        <div className="bg-gradient-to-r from-indigo-950/40 via-slate-900 to-indigo-950/30 border border-indigo-500/20 rounded-2xl p-5 mb-8 shadow-xl">
          <div className="flex items-center space-x-2 text-indigo-300 text-xs font-bold uppercase tracking-wider mb-3">
            <Lightbulb className="w-4 h-4 text-indigo-400" />
            <span>Executive Takeaways</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {insightsData.executive_takeaways.map((takeaway, idx) => (
              <div
                key={idx}
                className="flex items-start space-x-2 bg-slate-900/80 p-3 rounded-xl border border-slate-800 text-xs text-slate-300"
              >
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                <span>{takeaway}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Insights Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {insightsData.insights.map((item) => {
          const isHigh = item.importance === 'high';

          return (
            <div
              key={item.id}
              className="bg-slate-900/80 border border-slate-800 hover:border-slate-700 rounded-xl p-5 shadow-lg flex flex-col justify-between transition group"
            >
              <div>
                {/* Category & Importance */}
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    <div className="p-1.5 rounded-lg bg-slate-800 border border-slate-700">
                      {getCategoryIcon(item.category)}
                    </div>
                    <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                      {item.category}
                    </span>
                  </div>

                  <span
                    className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full border ${
                      isHigh
                        ? 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                        : 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30'
                    }`}
                  >
                    {item.importance} Impact
                  </span>
                </div>

                {/* Title & Description */}
                <h3 className="text-sm font-semibold text-white mb-2 group-hover:text-indigo-200 transition">
                  {item.title}
                </h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  {item.description}
                </p>
              </div>

              {/* Evidence details footer */}
              {Object.keys(item.evidence).length > 0 && (
                <div className="mt-4 pt-3 border-t border-slate-800/80 flex flex-wrap items-center gap-2 text-[11px] text-slate-500">
                  <span className="font-semibold text-slate-400">Evidence:</span>
                  {Object.entries(item.evidence).map(([k, v]) => (
                    <span key={k} className="bg-slate-800 px-2 py-0.5 rounded text-slate-300 font-mono">
                      {k.replace(/_/g, ' ')}: {typeof v === 'number' ? v : String(v)}
                    </span>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
