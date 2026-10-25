import React from 'react';
import {
  Upload,
  BarChart3,
  Sparkles,
  BrainCircuit,
  MessageSquareCode,
  FileSpreadsheet,
  Trash2,
  ExternalLink,
  Layers,
  ArrowRight,
  TrendingUp,
  ShieldCheck,
  Zap,
  Activity
} from 'lucide-react';
import { DatasetItem } from '../types';

interface WorkspaceHomeViewProps {
  datasets: DatasetItem[];
  onOpenUpload: () => void;
  onSelectDataset: (id: string, initialTab?: string) => void;
  onLoadSample: (sampleKey: string) => void;
  onDeleteDataset: (id: string) => void;
  isLoading: boolean;
}

export const WorkspaceHomeView: React.FC<WorkspaceHomeViewProps> = ({
  datasets,
  onOpenUpload,
  onSelectDataset,
  onLoadSample,
  onDeleteDataset,
  isLoading
}) => {
  const sampleDomains = [
    {
      key: 'cfpb',
      title: 'CFPB Consumer Financial Complaints',
      domain: 'Consumer Finance',
      badge: 'Flagship BI',
      records: '2,500 complaints',
      description: 'Overview, Company Responses, Issue Treemap, Product Horizontal Rankings, and Geographic Division Slices.',
      color: 'from-purple-600/30 to-indigo-600/30 border-purple-500/50 text-purple-300'
    },
    {
      key: 'sales',
      title: 'Global Sales & Profitability',
      domain: 'Sales & Revenue',
      badge: 'B2B & Retail',
      records: '1,000 orders',
      description: 'Regional revenue, profit margins, product velocity, and discount impact analytics.',
      color: 'from-blue-600/20 to-indigo-600/20 border-blue-500/30 text-blue-400'
    },
    {
      key: 'education',
      title: 'Student Academic Performance',
      domain: 'Higher Education',
      badge: 'Academic Analytics',
      records: '800 students',
      description: 'Attendance rates, study hours, midterm marks, department distributions, and final grades.',
      color: 'from-emerald-600/20 to-teal-600/20 border-emerald-500/30 text-emerald-400'
    },
    {
      key: 'healthcare',
      title: 'Hospital Diagnostics & Care',
      domain: 'Healthcare & Clinical',
      badge: 'Patient Analytics',
      records: '600 patients',
      description: 'Blood pressure, cholesterol, clinical diagnoses, length of stay, and treatment costs.',
      color: 'from-rose-600/20 to-pink-600/20 border-rose-500/30 text-rose-400'
    },
    {
      key: 'finance',
      title: 'Corporate Financial Transactions',
      domain: 'Treasury & Audit',
      badge: 'Fraud & Expenditure',
      records: '1,200 transactions',
      description: 'Account types, categorical spending, approval workflows, and anomaly flags.',
      color: 'from-amber-600/20 to-orange-600/20 border-amber-500/30 text-amber-400'
    }
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-10 animate-fadeIn">
      
      {/* Hero Welcome Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-slate-900 via-indigo-950/60 to-slate-900 border border-slate-800 p-8 sm:p-10 shadow-2xl">
        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 text-xs font-semibold uppercase tracking-wider mb-4">
            <Zap className="w-3.5 h-3.5" />
            <span>Autonomous Business Intelligence Studio</span>
          </div>

          <h1 className="text-3xl sm:text-4xl font-black text-white tracking-tight leading-tight">
            Connect Any Dataset. <br />
            <span className="bg-gradient-to-r from-indigo-400 via-cyan-300 to-indigo-300 bg-clip-text text-transparent">
              Automatic Power BI-Class Analytics & Predictive AI.
            </span>
          </h1>

          <p className="text-sm text-slate-300 mt-3 leading-relaxed max-w-2xl">
            Upload arbitrary CSV, Excel, JSON, or Parquet datasets without hardcoded schemas.
            DataMind AI profiles dynamic attributes, constructs interactive dashboards, enables natural language SQL chat, and trains predictive models on demand.
          </p>

          <div className="flex flex-wrap items-center gap-3 mt-6">
            <button
              onClick={() => onLoadSample('cfpb')}
              className="flex items-center space-x-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white text-xs font-bold px-5 py-3 rounded-xl shadow-lg shadow-purple-600/30 transition active:scale-95"
            >
              <BarChart3 className="w-4 h-4 text-purple-200" />
              <span>Launch CFPB Dashboard (Reference Theme)</span>
            </button>
            <button
              onClick={onOpenUpload}
              className="flex items-center space-x-2 bg-slate-800/90 hover:bg-slate-800 text-slate-200 text-xs font-semibold px-4 py-3 rounded-xl border border-slate-700 transition"
            >
              <Upload className="w-4 h-4" />
              <span>Upload Custom Dataset</span>
            </button>
          </div>
        </div>

        {/* Ambient Gradient Circles */}
        <div className="absolute top-0 right-0 -mr-16 -mt-16 w-80 h-80 rounded-full bg-indigo-500/10 blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 right-40 w-60 h-60 rounded-full bg-cyan-500/10 blur-3xl pointer-events-none" />
      </div>

      {/* Pre-loaded Business Domain Showcases */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-bold text-white flex items-center space-x-2">
              <Layers className="w-4 h-4 text-indigo-400" />
              <span>Pre-loaded Business Domains</span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Instant one-click interactive analytics across realistic enterprise domains.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {sampleDomains.map((sample) => (
            <div
              key={sample.key}
              className="bg-slate-900/80 border border-slate-800 hover:border-slate-700/80 rounded-2xl p-5 shadow-lg flex flex-col justify-between transition hover:-translate-y-1 duration-200 group"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    {sample.domain}
                  </span>
                  <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full border ${sample.color}`}>
                    {sample.badge}
                  </span>
                </div>

                <h3 className="text-sm font-bold text-white group-hover:text-indigo-300 transition mb-1">
                  {sample.title}
                </h3>
                <span className="text-[11px] font-medium text-indigo-400 block mb-2">
                  {sample.records}
                </span>
                <p className="text-xs text-slate-400 leading-relaxed mb-4">
                  {sample.description}
                </p>
              </div>

              <button
                onClick={() => onLoadSample(sample.key)}
                className="w-full flex items-center justify-center space-x-2 bg-slate-800 hover:bg-indigo-600 hover:text-white text-slate-300 text-xs font-semibold py-2 rounded-xl transition border border-slate-700 group-hover:border-indigo-500/50"
              >
                <span>Explore Dashboard</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Active Workspaces & Datasets Library */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5 pb-4 border-b border-slate-800">
          <div>
            <h2 className="text-base font-bold text-white flex items-center space-x-2">
              <FileSpreadsheet className="w-4 h-4 text-indigo-400" />
              <span>Available Datasets & Reports ({datasets.length})</span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Click any dataset to open its auto-generated Power BI dashboard, AI chat, or predictive studio.
            </p>
          </div>

          <button
            onClick={onOpenUpload}
            className="flex items-center space-x-1.5 bg-indigo-600/90 hover:bg-indigo-600 text-white text-xs font-medium px-3.5 py-2 rounded-lg transition"
          >
            <Upload className="w-3.5 h-3.5" />
            <span>Add Dataset</span>
          </button>
        </div>

        {datasets.length === 0 ? (
          <div className="text-center py-12 text-slate-400">
            <Layers className="w-10 h-10 text-slate-600 mx-auto mb-3" />
            <p className="text-sm font-medium text-slate-300">No datasets found in workspace</p>
            <p className="text-xs text-slate-500 mt-1">Upload a CSV/Excel file or launch a sample domain above.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-800/80 text-slate-400 uppercase text-[10px] border-b border-slate-700">
                <tr>
                  <th className="px-4 py-3 font-semibold">Dataset Name</th>
                  <th className="px-4 py-3 font-semibold">Format</th>
                  <th className="px-4 py-3 font-semibold">Records</th>
                  <th className="px-4 py-3 font-semibold">Attributes</th>
                  <th className="px-4 py-3 font-semibold">Size</th>
                  <th className="px-4 py-3 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {datasets.map((d) => (
                  <tr key={d.id} className="hover:bg-slate-800/40 transition group">
                    <td className="px-4 py-3.5">
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 rounded-lg bg-indigo-600/10 text-indigo-400 border border-indigo-500/20 flex items-center justify-center shrink-0">
                          <BarChart3 className="w-4 h-4" />
                        </div>
                        <div>
                          <span
                            onClick={() => onSelectDataset(d.id, 'dashboard')}
                            className="font-semibold text-white group-hover:text-indigo-300 transition cursor-pointer hover:underline block"
                          >
                            {d.name}
                          </span>
                          <span className="text-[11px] text-slate-500 font-mono">{d.filename}</span>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3.5">
                      <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                        {d.file_format}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 font-mono text-slate-200">
                      {d.row_count.toLocaleString()}
                    </td>
                    <td className="px-4 py-3.5 font-mono text-slate-200">
                      {d.col_count} cols
                    </td>
                    <td className="px-4 py-3.5 font-mono text-slate-400">
                      {d.file_size_mb} MB
                    </td>
                    <td className="px-4 py-3.5 text-right">
                      <div className="flex items-center justify-end space-x-2">
                        <button
                          onClick={() => onSelectDataset(d.id, 'dashboard')}
                          className="bg-indigo-600 hover:bg-indigo-500 text-white text-[11px] font-semibold px-3 py-1.5 rounded-lg transition shadow-sm"
                        >
                          Dashboard
                        </button>
                        <button
                          onClick={() => onSelectDataset(d.id, 'chat')}
                          title="Ask AI Chat"
                          className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
                        >
                          <MessageSquareCode className="w-3.5 h-3.5 text-indigo-400" />
                        </button>
                        <button
                          onClick={() => onSelectDataset(d.id, 'predictive')}
                          title="Predictive Studio"
                          className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
                        >
                          <BrainCircuit className="w-3.5 h-3.5 text-cyan-400" />
                        </button>
                        <button
                          onClick={() => onDeleteDataset(d.id)}
                          title="Delete Dataset"
                          className="p-1.5 rounded-lg bg-slate-800 hover:bg-rose-950/60 text-slate-400 hover:text-rose-400 transition"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
