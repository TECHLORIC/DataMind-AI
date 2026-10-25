import React from 'react';
import {
  FileText,
  Printer,
  Download,
  X,
  CheckCircle2,
  ExternalLink,
  ShieldCheck,
  Sparkles
} from 'lucide-react';
import { DashboardSpec, DatasetProfile } from '../types';

interface ReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  datasetId: string;
  dashboard: DashboardSpec | null;
  profile: DatasetProfile | null;
}

export const ReportModal: React.FC<ReportModalProps> = ({
  isOpen,
  onClose,
  datasetId,
  dashboard,
  profile
}) => {
  if (!isOpen || !dashboard || !profile) return null;

  const handleDownloadPDF = () => {
    // Open print-to-pdf endpoint in new window
    window.open(`/api/v1/reports/pdf/${datasetId}`, '_blank');
  };

  const handleBrowserPrint = () => {
    window.print();
  };

  const handleDownloadJSON = () => {
    const reportData = {
      title: dashboard.title,
      dataset_name: profile.name,
      rows: profile.total_rows,
      columns: profile.total_columns,
      completeness: profile.completeness,
      kpis: dashboard.kpis,
      charts: dashboard.charts.map(c => ({
        title: c.title,
        type: c.chart_type,
        data: c.data,
        insight: c.insight
      }))
    };
    const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${profile.name.replace(/\s+/g, '_')}_Report.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-xl p-6 shadow-2xl relative">
        
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-white transition"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Modal Header */}
        <div className="flex items-center space-x-3 mb-5">
          <div className="w-10 h-10 rounded-xl bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 flex items-center justify-center">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-white">Download Analytical Report</h2>
            <p className="text-xs text-slate-400">
              Generate executive-ready PDF documents or download analytical summaries.
            </p>
          </div>
        </div>

        {/* Report Overview Preview Box */}
        <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-4 mb-6">
          <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800/80">
            <span className="text-xs font-bold text-white">{profile.name}</span>
            <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full">
              {profile.completeness}% Complete
            </span>
          </div>

          <div className="grid grid-cols-3 gap-2 text-center text-xs mb-3">
            <div className="bg-slate-900 p-2 rounded-lg">
              <span className="text-[10px] text-slate-400 block">Total Records</span>
              <span className="font-bold text-white">{profile.total_rows.toLocaleString()}</span>
            </div>
            <div className="bg-slate-900 p-2 rounded-lg">
              <span className="text-[10px] text-slate-400 block">KPI Metrics</span>
              <span className="font-bold text-white">{dashboard.kpis.length}</span>
            </div>
            <div className="bg-slate-900 p-2 rounded-lg">
              <span className="text-[10px] text-slate-400 block">Visualizations</span>
              <span className="font-bold text-white">{dashboard.charts.length}</span>
            </div>
          </div>

          <p className="text-[11px] text-slate-400 line-clamp-2 italic">
            "{dashboard.executive_summary}"
          </p>
        </div>

        {/* Download Options */}
        <div className="space-y-3 mb-6">
          {/* Main Action: True PDF Download */}
          <button
            onClick={handleDownloadPDF}
            className="w-full flex items-center justify-between p-3.5 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white font-semibold text-xs shadow-lg shadow-indigo-600/30 transition group"
          >
            <div className="flex items-center space-x-3">
              <Download className="w-4 h-4 text-white" />
              <div className="text-left">
                <div className="text-white font-bold">Download Executive PDF Report</div>
                <div className="text-[10px] text-indigo-100 font-normal">
                  Formatted for A4/Letter print with cover header, KPIs, data tables & insights
                </div>
              </div>
            </div>
            <ExternalLink className="w-4 h-4 text-indigo-200 group-hover:translate-x-0.5 transition" />
          </button>

          {/* Secondary Action: Print Screen */}
          <button
            onClick={handleBrowserPrint}
            className="w-full flex items-center justify-between p-3 rounded-xl bg-slate-800/80 hover:bg-slate-800 border border-slate-700 text-slate-200 text-xs font-medium transition"
          >
            <div className="flex items-center space-x-3">
              <Printer className="w-4 h-4 text-cyan-400" />
              <div className="text-left">
                <div className="font-semibold text-white">Print / Save Canvas as PDF</div>
                <div className="text-[10px] text-slate-400">
                  Sends current dashboard layout directly to browser print dialog
                </div>
              </div>
            </div>
            <span className="text-[10px] text-slate-400">Ctrl + P</span>
          </button>

          {/* Tertiary Action: Export JSON */}
          <button
            onClick={handleDownloadJSON}
            className="w-full flex items-center justify-between p-2.5 rounded-xl bg-slate-800/40 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-slate-200 text-xs transition"
          >
            <div className="flex items-center space-x-2">
              <FileText className="w-3.5 h-3.5" />
              <span>Export Raw Data & Aggregates (JSON)</span>
            </div>
            <span className="text-[10px] font-mono text-slate-500">.json</span>
          </button>
        </div>

        {/* Footer */}
        <div className="flex justify-end pt-3 border-t border-slate-800">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-white transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
