import React from 'react';
import {
  LayoutDashboard,
  BarChart3,
  MessageSquareCode,
  Sparkles,
  BrainCircuit,
  Database,
  Upload,
  ChevronDown,
  Layers,
  ArrowLeft
} from 'lucide-react';
import { DatasetItem } from '../types';

interface HeaderProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  datasets: DatasetItem[];
  selectedDatasetId: string;
  onSelectDataset: (id: string) => void;
  onLoadSample?: (sampleKey: string) => void;
  onOpenUpload: () => void;
  isLoading: boolean;
  onReturnHome: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  setActiveTab,
  datasets,
  selectedDatasetId,
  onSelectDataset,
  onLoadSample,
  onOpenUpload,
  isLoading,
  onReturnHome
}) => {
  const currentDataset = datasets.find(d => d.id === selectedDatasetId);

  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
    { id: 'chat', label: 'Ask Your Data', icon: MessageSquareCode },
    { id: 'insights', label: 'AI Insights', icon: Sparkles },
    { id: 'predictive', label: 'Predictive Studio', icon: BrainCircuit },
    { id: 'schema', label: 'Data & Schema', icon: Database },
  ];

  return (
    <header className="sticky top-0 z-40 bg-[#0f172a]/95 backdrop-blur-md border-b border-slate-800 text-slate-100">
      {/* Top Banner */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 gap-4">
          
          {/* Logo & Platform Title (Click to return home) */}
          <div
            onClick={onReturnHome}
            className="flex items-center space-x-3 cursor-pointer group"
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 p-0.5 shadow-lg shadow-indigo-500/20 flex items-center justify-center group-hover:scale-105 transition">
              <div className="w-full h-full bg-[#0f172a] rounded-[10px] flex items-center justify-center">
                <BarChart3 className="w-5 h-5 text-indigo-400" />
              </div>
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-white via-slate-100 to-indigo-200 bg-clip-text text-transparent">
                  DataMind AI
                </span>
                <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  Power BI Studio
                </span>
              </div>
              <p className="text-xs text-slate-400 hidden sm:block">
                Autonomous Business Intelligence & Predictive Analytics
              </p>
            </div>
          </div>

          {/* Dataset Selector & Quick Actions */}
          <div className="flex items-center space-x-3">
            
            {/* Return to Home / Workspace Pill */}
            <button
              onClick={onReturnHome}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition border ${
                activeTab === 'home'
                  ? 'bg-indigo-600 text-white border-indigo-500'
                  : 'bg-slate-900 text-slate-300 border-slate-700 hover:bg-slate-800'
              }`}
            >
              <LayoutDashboard className="w-3.5 h-3.5 text-indigo-400" />
              <span>Workspace Hub</span>
            </button>

            {/* Dataset Dropdown */}
            {datasets.length > 0 && (
              <div className="relative">
                <select
                  value={selectedDatasetId}
                  onChange={(e) => onSelectDataset(e.target.value)}
                  className="bg-slate-900 border border-slate-700/80 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 appearance-none pr-8 cursor-pointer max-w-[200px] truncate"
                >
                  <option value="" disabled>Select Dataset...</option>
                  {datasets.map(d => (
                    <option key={d.id} value={d.id}>
                      {d.name} ({d.row_count.toLocaleString()} rows)
                    </option>
                  ))}
                </select>
                <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
              </div>
            )}

            {/* Upload Button */}
            <button
              onClick={onOpenUpload}
              className="flex items-center space-x-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium px-3.5 py-1.5 rounded-lg transition shadow-md shadow-indigo-600/20 active:scale-95"
            >
              <Upload className="w-3.5 h-3.5" />
              <span>Upload Data</span>
            </button>
          </div>
        </div>

        {/* Navigation Tabs (visible when viewing a dataset) */}
        {selectedDatasetId && activeTab !== 'home' && (
          <div className="flex items-center justify-between border-t border-slate-800/60 pt-1 pb-1">
            <div className="flex space-x-1 overflow-x-auto scrollbar-none">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center space-x-2 px-3.5 py-1.5 text-xs font-medium rounded-lg transition whitespace-nowrap ${
                      isActive
                        ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 shadow-sm'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                    }`}
                  >
                    <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-indigo-400' : 'text-slate-400'}`} />
                    <span>{tab.label}</span>
                  </button>
                );
              })}
            </div>

            {currentDataset && (
              <div className="hidden md:flex items-center space-x-2 text-xs text-slate-400">
                <span className="font-semibold text-slate-200">{currentDataset.name}</span>
                <span>&bull;</span>
                <span className="font-mono text-[11px]">{currentDataset.row_count.toLocaleString()} rows</span>
              </div>
            )}
          </div>
        )}
      </div>
    </header>
  );
};
