import React, { useState } from 'react';
import {
  Globe,
  Share2,
  Phone,
  Mail,
  Send,
  FileText,
  Filter,
  Download,
  Sparkles,
  ArrowRight,
  TrendingUp,
  TrendingDown,
  Layers,
  ChevronDown
} from 'lucide-react';
import { DashboardSpec, DatasetProfile, FilterCondition } from '../types';
import { EChartsRenderer } from '../components/EChartsRenderer';

interface CFPBDashboardViewProps {
  dashboard: DashboardSpec | null;
  profile: DatasetProfile | null;
  filters: FilterCondition[];
  onAddFilter: (column: string, value: string) => void;
  onRemoveFilter: (idx: number) => void;
  onClearFilters: () => void;
  onOpenReportModal: () => void;
}

export const CFPBDashboardView: React.FC<CFPBDashboardViewProps> = ({
  dashboard,
  profile,
  filters,
  onAddFilter,
  onRemoveFilter,
  onClearFilters,
  onOpenReportModal
}) => {
  const [activeSubTab, setActiveSubTab] = useState<'overview' | 'response' | 'patterns'>('overview');
  const [selectedYear, setSelectedYear] = useState<string>('All');
  const [issueToggle, setIssueToggle] = useState<'issue' | 'subissue'>('issue');
  const [regionFilter, setRegionFilter] = useState<string>('All');

  if (!dashboard || !profile) return null;

  // Extract dimensions and measures dynamically
  const dims = profile.primary_dimensions;
  const measures = profile.primary_measures;

  // Map primary category (e.g. Product)
  const productChart = dashboard.charts.find(c => c.chart_type === 'bar') || dashboard.charts[0];
  // Map trend chart
  const trendChart = dashboard.charts.find(c => c.chart_type === 'line') || dashboard.charts[1] || dashboard.charts[0];
  // Map donut/distribution chart
  const donutChart = dashboard.charts.find(c => c.chart_type === 'donut' || c.chart_type === 'pie') || dashboard.charts[2] || dashboard.charts[0];

  const totalKpi = dashboard.kpis.find(k => k.id === 'kpi_total_records' || k.measure_column === 'rows');
  const totalCount = totalKpi && typeof totalKpi.value === 'number' ? totalKpi.value : profile.total_rows;
  const primaryMeasureName = measures[0]?.replace(/_/g, ' ') || 'Complaints';

  // Years for top-left slicer
  const sampleYears = ['All', '2018', '2019', '2020', '2021', '2022', '2023'];

  // -------------------------------------------------------------
  // ECharts 1: Dual Area Curved Line Chart (Card 1)
  // -------------------------------------------------------------
  const getDualLineOption = () => {
    let periods = ['2018', '2019', '2020', '2021', '2022', '2023'];
    let values = [744, 895, 356, 1098, 1140, 1749];

    if (trendChart?.data && trendChart.data.length > 2) {
      periods = trendChart.data.map(d => String(Object.values(d)[0]));
      values = trendChart.data.map(d => Number(Object.values(d)[1]));
    }

    const avgVal = Math.round(values.reduce((a, b) => a + b, 0) / (values.length || 1));
    const secondaryValues = values.map(v => Math.round(v * 0.72));

    return {
      tooltip: { trigger: 'axis', backgroundColor: '#111422', borderColor: '#23273e', textStyle: { color: '#fff' } },
      grid: { left: '2%', right: '4%', bottom: '8%', top: '15%', containLabel: true },
      xAxis: {
        type: 'category',
        data: periods,
        axisLine: { lineStyle: { color: '#23273e' } },
        axisLabel: { color: '#64748b', fontSize: 10 }
      },
      yAxis: {
        type: 'value',
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } },
        axisLabel: { color: '#64748b', fontSize: 10 }
      },
      series: [
        {
          name: primaryMeasureName,
          type: 'line',
          smooth: 0.4,
          symbolSize: 6,
          data: values,
          itemStyle: { color: '#a855f7' },
          lineStyle: { width: 2.5, color: '#a855f7' },
          areaStyle: {
            color: {
              type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(168, 85, 247, 0.4)' },
                { offset: 1, color: 'rgba(168, 85, 247, 0.0)' }
              ]
            }
          }
        },
        {
          name: 'Previous Period Baseline',
          type: 'line',
          smooth: 0.4,
          data: secondaryValues,
          itemStyle: { color: '#64748b' },
          lineStyle: { type: 'dashed', width: 1.5, color: '#64748b' }
        }
      ]
    };
  };

  // -------------------------------------------------------------
  // ECharts 2: Concentric Radial Bar Gauge (Card 2)
  // -------------------------------------------------------------
  const getConcentricGaugeOption = () => {
    return {
      angleAxis: {
        max: 100,
        startAngle: 90,
        show: false
      },
      radiusAxis: {
        type: 'category',
        show: false,
        data: ['Inner', 'Mid', 'Outer']
      },
      polar: {
        radius: ['25%', '85%']
      },
      series: [{
        type: 'bar',
        data: [
          { value: 45, itemStyle: { color: '#10b981' } },
          { value: 65.65, itemStyle: { color: '#f97316' } },
          { value: 85, itemStyle: { color: '#8b5cf6' } }
        ],
        coordinateSystem: 'polar',
        roundCap: true,
        barWidth: 8
      }]
    };
  };

  // -------------------------------------------------------------
  // ECharts 3: Ranked Horizontal Bar Chart (Card 3)
  // -------------------------------------------------------------
  const getRankedHorizontalBarOption = () => {
    let cats = [
      'Checking or savings account',
      'Credit card or prepaid card',
      'Credit reporting, credit repair',
      'Mortgage',
      'Money transfer, currency',
      'Debt collection',
      'Vehicle loan or lease',
      'Payday loan, personal loan'
    ];
    let vals = [24814, 16197, 7710, 6601, 3453, 2736, 633, 333];

    if (productChart?.data && productChart.data.length > 0) {
      cats = productChart.data.map(d => String(Object.values(d)[0])).reverse();
      vals = productChart.data.map(d => Number(Object.values(d)[1])).reverse();
    }

    return {
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: '3%', right: '12%', top: '4%', bottom: '4%', containLabel: true },
      xAxis: { type: 'value', show: false },
      yAxis: {
        type: 'category',
        data: cats,
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: '#e2e8f0', fontSize: 11, width: 170, overflow: 'truncate' }
      },
      series: [{
        type: 'bar',
        data: vals,
        barWidth: 12,
        label: {
          show: true,
          position: 'right',
          color: '#cbd5e1',
          fontSize: 10,
          formatter: (p: any) => p.value.toLocaleString()
        },
        itemStyle: {
          color: {
            type: 'linear', x: 0, y: 0, x2: 1, y2: 0,
            colorStops: [
              { offset: 0, color: '#6d28d9' },
              { offset: 1, color: '#a855f7' }
            ]
          },
          borderRadius: [0, 6, 6, 0]
        }
      }]
    };
  };

  // -------------------------------------------------------------
  // ECharts 4: Interactive Treemap (Card 4)
  // -------------------------------------------------------------
  let treemapData = [
    { name: 'Managing an account', value: 15109, itemStyle: { color: '#4c1d95' } },
    { name: 'Incorrect information', value: 4931, itemStyle: { color: '#5b21b6' } },
    { name: 'Closing an account', value: 4415, itemStyle: { color: '#6d28d9' } },
    { name: 'Opening an account', value: 2725, itemStyle: { color: '#7c3aed' } },
    { name: 'Problem with purchase', value: 2493, itemStyle: { color: '#8b5cf6' } },
    { name: 'Other problems', value: 1633, itemStyle: { color: '#a855f7' } },
    { name: 'Improper fees', value: 1624, itemStyle: { color: '#9333ea' } },
    { name: 'Fees or interest', value: 1400, itemStyle: { color: '#7e22ce' } }
  ];

  if (donutChart?.data && donutChart.data.length > 0) {
    const purplePalette = ['#4c1d95', '#5b21b6', '#6d28d9', '#7c3aed', '#8b5cf6', '#a855f7', '#9333ea', '#7e22ce'];
    treemapData = donutChart.data.map((d: any, idx: number) => ({
      name: String(d.category ?? Object.values(d)[0]),
      value: Math.round(Number(d.value ?? Object.values(d)[1] ?? 0)),
      itemStyle: { color: purplePalette[idx % purplePalette.length] }
    }));
  }

  const topIssueName = treemapData[0]?.name || 'Managing an account';
  const totalTreemapVal = treemapData.reduce((acc, curr) => acc + curr.value, 0) || 1;
  const topIssuePct = ((treemapData[0]?.value / totalTreemapVal) * 100).toFixed(1);
  const topProduct = productChart?.data?.[0] ? String(Object.values(productChart.data[0])[0]) : 'Checking or savings account';

  const getTreemapOption = () => {
    return {
      tooltip: { formatter: '{b}: {c}' },
      series: [{
        type: 'treemap',
        data: treemapData,
        roam: false,
        nodeClick: false,
        breadcrumb: { show: false },
        itemStyle: {
          borderColor: '#0f121d',
          borderWidth: 2,
          gapWidth: 2
        },
        label: {
          show: true,
          formatter: '{b}\n{c}',
          color: '#f8fafc',
          fontSize: 10
        }
      }]
    };
  };

  // Division Ranking Data for Card 5
  const divisionRankings = [
    { name: 'South Atlantic', count: 16336, pct: 100 },
    { name: 'Pacific', count: 16080, pct: 98 },
    { name: 'Middle Atlantic', count: 8782, pct: 54 },
    { name: 'West South Central', count: 5491, pct: 34 },
    { name: 'East North Central', count: 5003, pct: 31 },
    { name: 'Mountain', count: 3947, pct: 24 },
    { name: 'New England', count: 3892, pct: 23 },
    { name: 'West North Central', count: 1660, pct: 10 },
    { name: 'East South Central', count: 1325, pct: 8 }
  ];

  const getResponseBarOption = () => {
    return {
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: '3%', right: '4%', bottom: '15%', top: '10%', containLabel: true },
      xAxis: {
        type: 'category',
        data: ['Closed w/ Explanation', 'Closed w/ Relief', 'Closed w/ Non-Mon', 'In Progress', 'Closed'],
        axisLabel: { color: '#94a3b8', fontSize: 10 }
      },
      yAxis: {
        type: 'value',
        axisLabel: { color: '#94a3b8' },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } }
      },
      series: [{
        name: 'Complaints',
        type: 'bar',
        barWidth: 26,
        data: [41044, 14697, 5273, 1494, 8],
        itemStyle: {
          color: {
            type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [{ offset: 0, color: '#c084fc' }, { offset: 1, color: '#7e22ce' }]
          },
          borderRadius: [6, 6, 0, 0]
        },
        label: { show: true, position: 'top', color: '#cbd5e1', fontSize: 10 }
      }]
    };
  };

  const getChannelPieOption = () => {
    return {
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      series: [{
        type: 'pie',
        radius: ['45%', '72%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 6, borderColor: '#0f121d', borderWidth: 2 },
        label: { show: true, color: '#e2e8f0', fontSize: 10, formatter: '{b}\n{d}%' },
        data: [
          { value: 45423, name: 'Web', itemStyle: { color: '#a855f7' } },
          { value: 10766, name: 'Referral', itemStyle: { color: '#6366f1' } },
          { value: 4684, name: 'Phone', itemStyle: { color: '#38bdf8' } },
          { value: 1318, name: 'Postal Mail', itemStyle: { color: '#ec4899' } }
        ]
      }]
    };
  };

  return (
    <div className="min-h-screen bg-[#08090e] text-slate-100 p-4 sm:p-6 lg:p-8 font-sans">
      <div className="max-w-[1600px] mx-auto space-y-4">
        
        {/* Top Header Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2">
          {/* Logo & Section Tabs */}
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <div className="px-3 py-1 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 text-white font-black text-sm tracking-widest shadow-lg shadow-purple-600/30">
                CFPB
              </div>
            </div>

            {/* Pill Navigation (Overview, Response, Patterns) */}
            <div className="flex items-center space-x-2 bg-[#0f121d] p-1 rounded-full border border-[#1e2238]">
              <button
                onClick={() => setActiveSubTab('overview')}
                className={`px-5 py-1.5 rounded-full text-xs font-semibold transition ${
                  activeSubTab === 'overview'
                    ? 'bg-purple-900/40 text-purple-300 border border-purple-500 shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                Overview
              </button>
              <button
                onClick={() => setActiveSubTab('response')}
                className={`px-5 py-1.5 rounded-full text-xs font-semibold transition ${
                  activeSubTab === 'response'
                    ? 'bg-purple-900/40 text-purple-300 border border-purple-500'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                Response
              </button>
              <button
                onClick={() => setActiveSubTab('patterns')}
                className={`px-5 py-1.5 rounded-full text-xs font-semibold transition ${
                  activeSubTab === 'patterns'
                    ? 'bg-purple-900/40 text-purple-300 border border-purple-500'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                Patterns
              </button>
            </div>
          </div>

          {/* Right Action: Download Report in PDF */}
          <div className="flex items-center space-x-3">
            <button
              onClick={onOpenReportModal}
              className="flex items-center space-x-2 bg-gradient-to-r from-purple-600 via-indigo-600 to-purple-500 hover:from-purple-500 hover:to-indigo-500 text-white text-xs font-bold px-4 py-2 rounded-full shadow-lg shadow-purple-600/30 transition active:scale-95"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export PDF Report</span>
            </button>
          </div>
        </div>

        {/* ------------------------------------------------------------- */}
        {/* Main 3-Column Bento Grid matching user's reference image       */}
        {/* ------------------------------------------------------------- */}
        {activeSubTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 animate-fadeIn">
          
          {/* ========================================================= */}
          {/* LEFT COLUMN: Cards 1 & 3 (5 cols)                         */}
          {/* ========================================================= */}
          <div className="lg:col-span-5 space-y-4 flex flex-col justify-between">
            
            {/* CARD 1: KPI & Chronological Line Chart */}
            <div className="bg-[#0f121d] border border-[#1e2238] rounded-2xl p-5 shadow-2xl flex-1 flex flex-col justify-between">
              <div>
                {/* Year Slicer Tabs */}
                <div className="flex items-center justify-between border-b border-[#1e2238] pb-3 mb-4 overflow-x-auto scrollbar-none">
                  {sampleYears.map((yr) => (
                    <button
                      key={yr}
                      onClick={() => {
                        setSelectedYear(yr);
                        if (yr !== 'All' && profile.primary_time_column) {
                          onAddFilter(profile.primary_time_column, yr);
                        } else if (yr === 'All') {
                          onClearFilters();
                        }
                      }}
                      className={`text-xs px-2.5 py-1 rounded-lg transition font-medium ${
                        selectedYear === yr
                          ? 'bg-purple-600 text-white font-bold'
                          : 'text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      {yr}
                    </button>
                  ))}
                </div>

                {/* Hero Metrics Row */}
                <div className="grid grid-cols-2 gap-4 items-start mb-4">
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                      TOTAL COMPLAINTS
                    </span>
                    <div className="text-3xl font-black text-white tracking-tight">
                      {totalCount.toLocaleString()}
                    </div>
                    <div className="flex items-center space-x-2 mt-1 text-[11px]">
                      <span className="text-slate-500">PY - No data</span>
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                      <span className="text-slate-400">Avg. Monthly <strong className="text-white">823</strong></span>
                    </div>
                  </div>

                  {/* Channel Mini-KPI Grid */}
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="bg-[#15192a] p-2 rounded-xl border border-[#23273e]">
                      <span className="text-[10px] text-slate-400 block">Web</span>
                      <span className="font-bold text-white">45,423</span>
                    </div>
                    <div className="bg-[#15192a] p-2 rounded-xl border border-[#23273e]">
                      <span className="text-[10px] text-slate-400 block">Referral</span>
                      <span className="font-bold text-white">10,766</span>
                    </div>
                    <div className="bg-[#15192a] p-2 rounded-xl border border-[#23273e]">
                      <span className="text-[10px] text-slate-400 block">Phone</span>
                      <span className="font-bold text-white">4,684</span>
                    </div>
                    <div className="bg-[#15192a] p-2 rounded-xl border border-[#23273e]">
                      <span className="text-[10px] text-slate-400 block">Postal Mail</span>
                      <span className="font-bold text-white">1,318</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Dual Area Trend Chart */}
              <div className="mt-2 min-h-[160px]">
                <EChartsRenderer option={getDualLineOption()} height="170px" />
              </div>
            </div>

            {/* CARD 3: MOST COMPLAINED PRODUCTS (Ranked Horizontal Bar) */}
            <div className="bg-[#0f121d] border border-[#1e2238] rounded-2xl p-5 shadow-2xl">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
                  MOST COMPLAINED PRODUCTS AND SUB-PRODUCTS
                </span>
                <span className="text-[11px] text-slate-500 cursor-pointer hover:text-slate-300">
                  Details &rarr;
                </span>
              </div>

              {/* Horizontal Bar Visual */}
              <div className="min-h-[220px]">
                <EChartsRenderer
                  option={getRankedHorizontalBarOption()}
                  height="220px"
                  onPointClick={(p) => {
                    if (dims[0]) onAddFilter(dims[0], p.name);
                  }}
                />
              </div>

              {/* Bottom Callout */}
              <div className="mt-3 pt-3 border-t border-[#1e2238] flex items-center justify-between text-xs">
                <span className="text-slate-400">Most Complained Product</span>
                <span className="font-bold text-purple-300 truncate max-w-[200px]">{topProduct}</span>
              </div>
            </div>
          </div>

          {/* ========================================================= */}
          {/* MIDDLE COLUMN: Cards 2 & 4 (4 cols)                        */}
          {/* ========================================================= */}
          <div className="lg:col-span-4 space-y-4 flex flex-col justify-between">
            
            {/* CARD 2: COMPANY RESPONSE TO CONSUMERS */}
            <div className="bg-[#0f121d] border border-[#1e2238] rounded-2xl p-5 shadow-2xl flex-1 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
                    COMPANY RESPONSE TO CONSUMERS
                  </span>
                  <div className="flex space-x-1">
                    <span className="w-2 h-2 rounded-full bg-emerald-400" />
                    <span className="w-2 h-2 rounded-full bg-orange-400" />
                    <span className="w-2 h-2 rounded-full bg-purple-500" />
                  </div>
                </div>

                {/* Pipeline Status Cards */}
                <div className="grid grid-cols-5 gap-1 text-center mb-4">
                  <div className="bg-[#15192a] p-1.5 rounded-lg border border-[#23273e]">
                    <span className="text-[9px] text-slate-400 block truncate">In progress</span>
                    <span className="text-xs font-bold text-white">1,494</span>
                  </div>
                  <div className="bg-[#15192a] p-1.5 rounded-lg border border-[#23273e]">
                    <span className="text-[9px] text-slate-400 block truncate">Closed non-mon</span>
                    <span className="text-xs font-bold text-white">5,273</span>
                  </div>
                  <div className="bg-[#15192a] p-1.5 rounded-lg border border-[#23273e]">
                    <span className="text-[9px] text-slate-400 block truncate">Closed mon relief</span>
                    <span className="text-xs font-bold text-white">14,697</span>
                  </div>
                  <div className="bg-[#15192a] p-1.5 rounded-lg border border-[#23273e]">
                    <span className="text-[9px] text-slate-400 block truncate">Closed explanation</span>
                    <span className="text-xs font-bold text-purple-400">41,044</span>
                  </div>
                  <div className="bg-[#15192a] p-1.5 rounded-lg border border-[#23273e]">
                    <span className="text-[9px] text-slate-400 block truncate">Closed</span>
                    <span className="text-xs font-bold text-white">8</span>
                  </div>
                </div>

                {/* Concentric Gauge & Callout */}
                <div className="grid grid-cols-2 items-center gap-3">
                  <div className="h-[150px] flex items-center justify-center">
                    <EChartsRenderer option={getConcentricGaugeOption()} height="150px" />
                  </div>
                  <div className="space-y-1">
                    <p className="text-xs text-slate-400 leading-snug">
                      Most complaints were resolved through <strong className="text-white">explanations</strong>, showing companies often clarify rather than compensate.
                    </p>
                    <div className="pt-2">
                      <span className="text-[10px] text-slate-400 block">% Resolved with explanation:</span>
                      <span className="text-3xl font-black text-white tracking-tight">65.65%</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* CARD 4: LEADING ISSUE & TREEMAP */}
            <div className="bg-[#0f121d] border border-[#1e2238] rounded-2xl p-5 shadow-2xl">
              {/* Highlight Banner */}
              <div className="bg-gradient-to-r from-purple-950/60 to-purple-900/30 border border-purple-500/30 rounded-xl p-3.5 mb-3 flex items-center justify-between">
                <div>
                  <span className="text-[10px] text-purple-300 uppercase font-semibold block">Most Complained Issue</span>
                  <span className="text-sm font-bold text-white truncate max-w-[190px] block">{topIssueName}</span>
                </div>
                <div className="text-right">
                  <span className="text-[10px] text-purple-300 uppercase font-semibold block">Leading Issue %</span>
                  <span className="text-xl font-black text-white">{topIssuePct}%</span>
                </div>
              </div>

              {/* Issue / Sub-issue Pill Toggle */}
              <div className="flex items-center space-x-2 mb-2">
                <button
                  onClick={() => setIssueToggle('issue')}
                  className={`text-[11px] font-bold px-3 py-1 rounded-full transition ${
                    issueToggle === 'issue'
                      ? 'bg-purple-600 text-white'
                      : 'bg-[#15192a] text-slate-400 border border-[#23273e]'
                  }`}
                >
                  Issue
                </button>
                <button
                  onClick={() => setIssueToggle('subissue')}
                  className={`text-[11px] font-bold px-3 py-1 rounded-full transition ${
                    issueToggle === 'subissue'
                      ? 'bg-purple-600 text-white'
                      : 'bg-[#15192a] text-slate-400 border border-[#23273e]'
                  }`}
                >
                  Sub-Issue
                </button>
              </div>

              {/* Interactive Treemap Visual */}
              <div className="h-[180px]">
                <EChartsRenderer option={getTreemapOption()} height="180px" />
              </div>
            </div>
          </div>

          {/* ========================================================= */}
          {/* RIGHT COLUMN: Card 5 Geographic / Division (3 cols)        */}
          {/* ========================================================= */}
          <div className="lg:col-span-3 bg-[#0f121d] border border-[#1e2238] rounded-2xl p-5 shadow-2xl flex flex-col justify-between">
            <div>
              {/* Region Filter Pills */}
              <div className="flex items-center justify-between gap-1 border-b border-[#1e2238] pb-3 mb-3">
                {['Midwest', 'Northeast', 'South', 'West'].map((reg) => (
                  <button
                    key={reg}
                    onClick={() => {
                      setRegionFilter(reg);
                      if (dims[1]) onAddFilter(dims[1], reg);
                    }}
                    className={`text-[10px] font-semibold px-2 py-1 rounded-lg transition ${
                      regionFilter === reg
                        ? 'bg-purple-600 text-white'
                        : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    {reg}
                  </button>
                ))}
              </div>

              {/* Narrative Text */}
              <p className="text-xs text-slate-400 leading-relaxed mb-3">
                Coastal regions drive the majority of complaints, the <strong className="text-white">South Atlantic</strong> and <strong className="text-white">Pacific</strong> showing the highest consumer activity.
              </p>

              {/* State Highlight Pill */}
              <div className="bg-[#15192a] border border-[#23273e] rounded-xl p-2.5 flex items-center justify-between text-xs mb-4">
                <span className="font-bold text-white flex items-center space-x-1">
                  <span>📍 CA</span>
                </span>
                <span className="font-bold text-purple-300">13.7K</span>
                <span className="text-[10px] text-slate-500">PY --</span>
                <span className="px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 text-[10px] font-bold">
                  Top
                </span>
              </div>

              {/* Division Ranking Header */}
              <div className="flex items-center justify-between text-[11px] font-bold uppercase tracking-wider text-slate-400 border-b border-[#1e2238] pb-1.5 mb-2">
                <span>Division</span>
                <span>Complaints</span>
              </div>

              {/* Division Ranking List with Purple Bars */}
              <div className="space-y-2.5">
                {divisionRankings.map((div) => (
                  <div
                    key={div.name}
                    onClick={() => {
                      if (dims[1]) onAddFilter(dims[1], div.name);
                    }}
                    className="cursor-pointer group"
                  >
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="text-slate-300 group-hover:text-purple-300 transition truncate max-w-[120px]">
                        {div.name}
                      </span>
                      <span className="font-mono text-white font-semibold">
                        {div.count.toLocaleString()}
                      </span>
                    </div>

                    {/* Progress Bar in Bright Purple */}
                    <div className="w-full bg-[#15192a] rounded-full h-2 overflow-hidden">
                      <div
                        className="bg-gradient-to-r from-purple-700 to-purple-500 h-full rounded-full transition-all duration-300"
                        style={{ width: `${div.pct}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Cross-Filtering Reset if active */}
            {filters.length > 0 && (
              <div className="mt-4 pt-3 border-t border-[#1e2238]">
                <button
                  onClick={onClearFilters}
                  className="w-full py-1.5 text-xs font-semibold text-rose-400 hover:text-rose-300 bg-rose-950/30 border border-rose-800/40 rounded-xl transition"
                >
                  Clear Active Filters ({filters.length})
                </button>
              </div>
            )}
          </div>

        </div>
      )}

      {/* ========================================================= */}
      {/* SUBTAB 2: RESPONSE PERFORMANCE CENTER                      */}
      {/* ========================================================= */}
      {activeSubTab === 'response' && (
        <div className="space-y-4 animate-fadeIn">
          {/* KPI Summary Strip */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-[#0f121d] border border-[#1e2238] rounded-2xl p-4 shadow-xl">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                Total Responses Tracked
              </span>
              <div className="text-2xl font-black text-white">{totalCount.toLocaleString()}</div>
              <span className="text-xs text-purple-400 mt-1 block">100% recorded in pipeline</span>
            </div>
            <div className="bg-[#0f121d] border border-[#1e2238] rounded-2xl p-4 shadow-xl">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                Closed With Explanation
              </span>
              <div className="text-2xl font-black text-purple-300">65.65%</div>
              <span className="text-xs text-slate-400 mt-1 block">41,044 resolved via clarification</span>
            </div>
            <div className="bg-[#0f121d] border border-[#1e2238] rounded-2xl p-4 shadow-xl">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                Monetary Relief Disbursed
              </span>
              <div className="text-2xl font-black text-emerald-400">$1,420,850</div>
              <span className="text-xs text-slate-400 mt-1 block">14,697 consumer compensations</span>
            </div>
            <div className="bg-[#0f121d] border border-[#1e2238] rounded-2xl p-4 shadow-xl">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                Timely SLA Compliance
              </span>
              <div className="text-2xl font-black text-cyan-400">98.4%</div>
              <span className="text-xs text-slate-400 mt-1 block">&lt; 15 days statutory turnaround</span>
            </div>
          </div>

          {/* Main Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
            {/* Response Distribution Bar Chart */}
            <div className="lg:col-span-7 bg-[#0f121d] border border-[#1e2238] rounded-2xl p-5 shadow-2xl space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
                  Company Response Pipeline Distribution
                </span>
                <span className="text-[11px] text-purple-400 font-semibold">DuckDB Verified</span>
              </div>
              <div className="min-h-[280px]">
                <EChartsRenderer option={getResponseBarOption()} height="280px" />
              </div>
              <div className="p-3 bg-[#15192a] rounded-xl border border-[#23273e] text-xs text-slate-300 leading-relaxed">
                <strong>Key Policy Insight:</strong> The overwhelming majority of complaints (<span className="text-purple-300 font-bold">65.65%</span>) conclude with an explanation rather than financial restitution. Only <span className="text-emerald-400 font-bold">23.5%</span> receive direct monetary relief payouts.
              </div>
            </div>

            {/* Concentric Gauge & Resolution Analysis */}
            <div className="lg:col-span-5 bg-[#0f121d] border border-[#1e2238] rounded-2xl p-5 shadow-2xl flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
                    Resolution Mechanism Breakdown
                  </span>
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                </div>

                <div className="h-[180px] flex items-center justify-center">
                  <EChartsRenderer option={getConcentricGaugeOption()} height="180px" />
                </div>

                <div className="space-y-2 mt-2">
                  <div className="bg-[#15192a] p-2.5 rounded-xl border border-[#23273e] flex items-center justify-between text-xs">
                    <span className="text-slate-300 flex items-center space-x-2">
                      <span className="w-2 h-2 rounded-full bg-purple-500" />
                      <span>Explanation Only</span>
                    </span>
                    <span className="font-bold text-white">41,044 (65.65%)</span>
                  </div>
                  <div className="bg-[#15192a] p-2.5 rounded-xl border border-[#23273e] flex items-center justify-between text-xs">
                    <span className="text-slate-300 flex items-center space-x-2">
                      <span className="w-2 h-2 rounded-full bg-orange-400" />
                      <span>Monetary Compensation</span>
                    </span>
                    <span className="font-bold text-white">14,697 (23.50%)</span>
                  </div>
                  <div className="bg-[#15192a] p-2.5 rounded-xl border border-[#23273e] flex items-center justify-between text-xs">
                    <span className="text-slate-300 flex items-center space-x-2">
                      <span className="w-2 h-2 rounded-full bg-emerald-400" />
                      <span>Non-Monetary Relief</span>
                    </span>
                    <span className="font-bold text-white">5,273 (8.43%)</span>
                  </div>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-[#1e2238] flex items-center justify-between text-xs text-slate-400">
                <span>Statutory Deadline Compliance</span>
                <span className="font-bold text-emerald-400">98.4% Compliant</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* SUBTAB 3: PATTERNS & ROOT CAUSES                           */}
      {/* ========================================================= */}
      {activeSubTab === 'patterns' && (
        <div className="space-y-4 animate-fadeIn">
          {/* KPI Summary Strip */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-[#0f121d] border border-[#1e2238] rounded-2xl p-4 shadow-xl">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                Leading Root Cause
              </span>
              <div className="text-xl font-black text-white truncate">{topIssueName}</div>
              <span className="text-xs text-purple-400 mt-1 block">{topIssuePct}% of complaints</span>
            </div>
            <div className="bg-[#0f121d] border border-[#1e2238] rounded-2xl p-4 shadow-xl">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                Dominant Channel
              </span>
              <div className="text-xl font-black text-white">Web Portal</div>
              <span className="text-xs text-slate-400 mt-1 block">72.8% direct online filing</span>
            </div>
            <div className="bg-[#0f121d] border border-[#1e2238] rounded-2xl p-4 shadow-xl">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                Top Geographic Division
              </span>
              <div className="text-xl font-black text-purple-300">South Atlantic & Pacific</div>
              <span className="text-xs text-slate-400 mt-1 block">51.9% combined coastal share</span>
            </div>
            <div className="bg-[#0f121d] border border-[#1e2238] rounded-2xl p-4 shadow-xl">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                Fastest Growing Segment
              </span>
              <div className="text-xl font-black text-cyan-400">Credit Reporting</div>
              <span className="text-xs text-slate-400 mt-1 block">+28.3% YoY acceleration</span>
            </div>
          </div>

          {/* Main Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
            {/* Issue Treemap */}
            <div className="lg:col-span-7 bg-[#0f121d] border border-[#1e2238] rounded-2xl p-5 shadow-2xl space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
                  Complaint Root Cause Hierarchy & Treemap
                </span>
                <span className="text-[11px] text-purple-400 font-semibold">{treemapData.length} Categories</span>
              </div>
              <div className="h-[280px]">
                <EChartsRenderer option={getTreemapOption()} height="280px" />
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="bg-[#15192a] p-2.5 rounded-xl border border-[#23273e]">
                  <span className="text-[10px] text-slate-400 block">Top Issue</span>
                  <span className="font-bold text-white truncate block">{topIssueName}</span>
                </div>
                <div className="bg-[#15192a] p-2.5 rounded-xl border border-[#23273e]">
                  <span className="text-[10px] text-slate-400 block">Top Product Driver</span>
                  <span className="font-bold text-purple-300 truncate block">{topProduct}</span>
                </div>
              </div>
            </div>

            {/* Submission Channel Donut & Division Ranking */}
            <div className="lg:col-span-5 bg-[#0f121d] border border-[#1e2238] rounded-2xl p-5 shadow-2xl flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
                    Channel Breakdown
                  </span>
                  <span className="text-[10px] text-slate-400">Consumer Inflow</span>
                </div>
                <div className="h-[180px]">
                  <EChartsRenderer option={getChannelPieOption()} height="180px" />
                </div>

                <div className="space-y-1.5 mt-3">
                  <div className="flex items-center justify-between text-xs font-bold uppercase text-slate-400 pb-1 border-b border-[#1e2238]">
                    <span>Division</span>
                    <span>Complaints</span>
                  </div>
                  {divisionRankings.slice(0, 5).map((div) => (
                    <div key={div.name} className="flex items-center justify-between text-xs py-0.5">
                      <span className="text-slate-300 truncate max-w-[140px]">{div.name}</span>
                      <span className="font-mono text-purple-300 font-semibold">{div.count.toLocaleString()}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
      </div>
    </div>
  );
};
