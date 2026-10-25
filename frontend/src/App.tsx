import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  DatasetItem,
  DatasetProfile,
  DashboardSpec,
  InsightsResponse,
  FilterCondition
} from './types';
import { Header } from './components/Header';
import { UploadModal } from './components/UploadModal';
import { ReportModal } from './components/ReportModal';
import { PowerBIDataPane } from './components/PowerBIDataPane';
import { WorkspaceHomeView } from './views/WorkspaceHomeView';
import { DashboardView } from './views/DashboardView';
import { CFPBDashboardView } from './views/CFPBDashboardView';
import { ChatView } from './views/ChatView';
import { InsightsView } from './views/InsightsView';
import { PredictiveStudioView } from './views/PredictiveStudioView';
import { DataSchemaView } from './views/DataSchemaView';
import { Loader2 } from 'lucide-react';

export function App() {
  // Default to clean Workspace Hub home interface!
  const [activeTab, setActiveTab] = useState<string>('home');
  const [datasets, setDatasets] = useState<DatasetItem[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>('');
  
  const [profile, setProfile] = useState<DatasetProfile | null>(null);
  const [dashboard, setDashboard] = useState<DashboardSpec | null>(null);
  const [insights, setInsights] = useState<InsightsResponse | null>(null);

  const [filters, setFilters] = useState<FilterCondition[]>([]);
  const [isFiltering, setIsFiltering] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  
  const [isUploadOpen, setIsUploadOpen] = useState<boolean>(false);
  const [isReportModalOpen, setIsReportModalOpen] = useState<boolean>(false);
  const [isDataPaneOpen, setIsDataPaneOpen] = useState<boolean>(false);
  const [dashboardLayout, setDashboardLayout] = useState<'cfpb' | 'grid'>('cfpb');

  // Fetch all datasets on startup
  const fetchDatasets = async () => {
    try {
      const res = await axios.get('/api/v1/datasets');
      setDatasets(res.data);
    } catch (err) {
      console.error('Failed to fetch datasets:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDatasets();
  }, []);

  // Fetch dataset details when selectedDatasetId changes
  useEffect(() => {
    if (!selectedDatasetId) return;

    const loadDatasetDetails = async () => {
      setIsLoading(true);
      setFilters([]);
      try {
        const res = await axios.get(`/api/v1/datasets/${selectedDatasetId}`);
        setProfile(res.data.profile);
        setDashboard(res.data.dashboard);
        setInsights(res.data.insights);
      } catch (err) {
        console.error('Failed to load dataset details:', err);
      } finally {
        setIsLoading(false);
      }
    };

    loadDatasetDetails();
  }, [selectedDatasetId]);

  // Handle cross filtering
  const handleAddFilter = async (column: string, value: string) => {
    const newFilters = [...filters.filter(f => f.column !== column), { column, operator: 'eq', value }];
    setFilters(newFilters);
    setIsFiltering(true);

    try {
      const res = await axios.post(`/api/v1/datasets/${selectedDatasetId}/dashboard/filter`, newFilters);
      setDashboard(res.data);
    } catch (err) {
      console.error('Failed to filter dashboard:', err);
    } finally {
      setIsFiltering(false);
    }
  };

  const handleRemoveFilter = async (index: number) => {
    const newFilters = filters.filter((_, i) => i !== index);
    setFilters(newFilters);
    setIsFiltering(true);

    try {
      const res = await axios.post(`/api/v1/datasets/${selectedDatasetId}/dashboard/filter`, newFilters);
      setDashboard(res.data);
    } catch (err) {
      console.error('Failed to filter dashboard:', err);
    } finally {
      setIsFiltering(false);
    }
  };

  const handleClearFilters = async () => {
    setFilters([]);
    setIsFiltering(true);
    try {
      const res = await axios.post(`/api/v1/datasets/${selectedDatasetId}/dashboard/filter`, []);
      setDashboard(res.data);
    } catch (err) {
      console.error('Failed to clear filters:', err);
    } finally {
      setIsFiltering(false);
    }
  };

  // Quick load domain sample
  const handleLoadSample = async (sampleKey: string) => {
    setIsLoading(true);
    try {
      const res = await axios.post(`/api/v1/datasets/load-sample/${sampleKey}`);
      await fetchDatasets();
      setSelectedDatasetId(res.data.dataset_id);
      setActiveTab('dashboard');
    } catch (err: any) {
      alert('Failed to load sample dataset: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectDataset = (id: string, initialTab: string = 'dashboard') => {
    setSelectedDatasetId(id);
    setActiveTab(initialTab);
  };

  const handleDeleteDataset = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this dataset?')) return;
    try {
      await axios.delete(`/api/v1/datasets/${id}`);
      await fetchDatasets();
      if (selectedDatasetId === id) {
        setSelectedDatasetId('');
        setActiveTab('home');
      }
    } catch (err: any) {
      alert('Failed to delete dataset: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleUploadSuccess = (data: any) => {
    fetchDatasets();
    setSelectedDatasetId(data.dataset_id);
    setActiveTab('dashboard');
  };

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-100 flex flex-col font-sans selection:bg-indigo-500/30 selection:text-indigo-200">
      
      {/* Top Header & Navigation */}
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        datasets={datasets}
        selectedDatasetId={selectedDatasetId}
        onSelectDataset={(id) => handleSelectDataset(id, 'dashboard')}
        onLoadSample={handleLoadSample}
        onOpenUpload={() => setIsUploadOpen(true)}
        isLoading={isLoading}
        onReturnHome={() => setActiveTab('home')}
      />

      {/* Main Content Canvas */}
      <main className="flex-1 pb-12">
        {isLoading && activeTab !== 'home' && !dashboard ? (
          <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-3">
            <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
            <span className="text-xs font-medium text-slate-400">
              Loading dataset analytics & initializing DuckDB...
            </span>
          </div>
        ) : (
          <>
            {/* 1. Clean Workspace Hub / Home Landing */}
            {activeTab === 'home' && (
              <WorkspaceHomeView
                datasets={datasets}
                onOpenUpload={() => setIsUploadOpen(true)}
                onSelectDataset={handleSelectDataset}
                onLoadSample={handleLoadSample}
                onDeleteDataset={handleDeleteDataset}
                isLoading={isLoading}
              />
            )}

            {/* 2. Interactive Power BI Dashboard (CFPB Theme or Standard Grid) */}
            {activeTab === 'dashboard' && (
              <div>
                {/* Layout Selector Sub-bar */}
                <div className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 pt-3 flex items-center justify-between text-xs">
                  <div className="flex items-center space-x-2">
                    <span className="text-[11px] text-slate-500 font-semibold uppercase">Layout Mode:</span>
                    <button
                      onClick={() => setDashboardLayout('cfpb')}
                      className={`px-3 py-1 rounded-full text-xs font-semibold transition ${
                        dashboardLayout === 'cfpb'
                          ? 'bg-purple-600 text-white shadow-md shadow-purple-600/30'
                          : 'bg-[#15192a] text-slate-400 hover:text-white border border-[#23273e]'
                      }`}
                    >
                      CFPB Executive Theme (Reference)
                    </button>
                    <button
                      onClick={() => setDashboardLayout('grid')}
                      className={`px-3 py-1 rounded-full text-xs font-semibold transition ${
                        dashboardLayout === 'grid'
                          ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                          : 'bg-[#15192a] text-slate-400 hover:text-white border border-[#23273e]'
                      }`}
                    >
                      Power BI Modular Grid
                    </button>
                  </div>
                </div>

                {dashboardLayout === 'cfpb' ? (
                  <CFPBDashboardView
                    dashboard={dashboard}
                    profile={profile}
                    filters={filters}
                    onAddFilter={handleAddFilter}
                    onRemoveFilter={handleRemoveFilter}
                    onClearFilters={handleClearFilters}
                    onOpenReportModal={() => setIsReportModalOpen(true)}
                  />
                ) : (
                  <DashboardView
                    dashboard={dashboard}
                    profile={profile}
                    filters={filters}
                    onAddFilter={handleAddFilter}
                    onRemoveFilter={handleRemoveFilter}
                    onClearFilters={handleClearFilters}
                    isFiltering={isFiltering}
                    onOpenReportModal={() => setIsReportModalOpen(true)}
                  />
                )}
              </div>
            )}

            {/* 3. Ask Your Data AI Chat */}
            {activeTab === 'chat' && (
              <ChatView
                datasetId={selectedDatasetId}
                profile={profile}
              />
            )}

            {/* 4. Automated AI Insights */}
            {activeTab === 'insights' && (
              <InsightsView
                insightsData={insights}
                onRefresh={async () => {
                  if (!selectedDatasetId) return;
                  const res = await axios.post('/api/v1/insights/generate', null, {
                    params: { dataset_id: selectedDatasetId }
                  });
                  setInsights(res.data);
                }}
                isLoading={isLoading}
              />
            )}

            {/* 5. Flexible Predictive Studio */}
            {activeTab === 'predictive' && (
              <PredictiveStudioView
                datasetId={selectedDatasetId}
                profile={profile}
              />
            )}

            {/* 6. Dynamic Data & Schema Inspector */}
            {activeTab === 'schema' && (
              <DataSchemaView
                datasetId={selectedDatasetId}
                profile={profile}
              />
            )}
          </>
        )}
      </main>

      {/* Power BI Fields Pane (Data Pane) */}
      {selectedDatasetId && activeTab !== 'home' && (
        <PowerBIDataPane
          profile={profile}
          isOpen={isDataPaneOpen}
          onToggle={() => setIsDataPaneOpen(!isDataPaneOpen)}
          onQuickFilter={handleAddFilter}
        />
      )}

      {/* Upload Dataset Modal */}
      <UploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onUploadSuccess={handleUploadSuccess}
      />

      {/* Download PDF Report Modal */}
      <ReportModal
        isOpen={isReportModalOpen}
        onClose={() => setIsReportModalOpen(false)}
        datasetId={selectedDatasetId}
        dashboard={dashboard}
        profile={profile}
      />
    </div>
  );
}

export default App;
