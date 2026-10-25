import React, { useState } from 'react';
import {
  BrainCircuit,
  Play,
  CheckCircle2,
  Sliders,
  BarChart2,
  Sparkles,
  Loader2,
  HelpCircle,
  TrendingUp,
  Layers,
  Award,
  GitCommit,
  Activity,
  ArrowRight
} from 'lucide-react';
import axios from 'axios';
import { DatasetProfile, MLTrainResponse, MLPredictResponse } from '../types';
import { EChartsRenderer } from '../components/EChartsRenderer';

interface PredictiveStudioViewProps {
  datasetId: string;
  profile: DatasetProfile | null;
}

export const PredictiveStudioView: React.FC<PredictiveStudioViewProps> = ({
  datasetId,
  profile
}) => {
  const [taskType, setTaskType] = useState<string>('auto');
  const [targetColumn, setTargetColumn] = useState<string>('');
  const [isTraining, setIsTraining] = useState<boolean>(false);
  const [modelResult, setModelResult] = useState<MLTrainResponse | null>(null);
  const [trainError, setTrainError] = useState<string | null>(null);

  // What-If Simulator state
  const [whatIfInputs, setWhatIfInputs] = useState<Record<string, any>>({});
  const [predictionResult, setPredictionResult] = useState<MLPredictResponse | null>(null);
  const [isPredicting, setIsPredicting] = useState<boolean>(false);

  // Diagnostics view tab
  const [activeDiagTab, setActiveDiagTab] = useState<'leaderboard' | 'fit' | 'target' | 'features'>('leaderboard');

  if (!profile) return null;

  const handleTrain = async () => {
    setIsTraining(true);
    setTrainError(null);
    setPredictionResult(null);

    try {
      const res = await axios.post('/api/v1/ml/train', {
        dataset_id: datasetId,
        task_type: taskType,
        target_column: targetColumn || undefined
      });
      setModelResult(res.data);
      setIsTraining(false);

      // Pre-fill initial what-if values from feature_meta
      const initialInputs: Record<string, any> = {};
      if (res.data.feature_meta) {
        Object.entries(res.data.feature_meta).forEach(([f, meta]: [string, any]) => {
          initialInputs[f] = meta.default ?? '';
        });
      } else {
        res.data.features_used.forEach((f: string) => {
          const colMeta = profile.columns.find(c => c.name === f);
          if (colMeta) {
            initialInputs[f] = colMeta.mean_val ?? colMeta.sample_values[0] ?? '';
          }
        });
      }
      setWhatIfInputs(initialInputs);
    } catch (err: any) {
      setIsTraining(false);
      setTrainError(err.response?.data?.detail || 'Model training failed.');
    }
  };

  const handlePredict = async () => {
    if (!modelResult) return;
    setIsPredicting(true);

    try {
      const res = await axios.post('/api/v1/ml/predict', {
        model_id: modelResult.model_id,
        features: whatIfInputs
      });
      setPredictionResult(res.data);
      setIsPredicting(false);
    } catch (err: any) {
      setIsPredicting(false);
      alert('Prediction failed: ' + (err.response?.data?.detail || err.message));
    }
  };

  // 1. Feature Importance Chart Option
  const getFeatureImportanceOption = () => {
    if (!modelResult || !modelResult.feature_importance.length) return null;
    const sorted = [...modelResult.feature_importance].reverse();

    return {
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: '3%', right: '8%', bottom: '5%', top: '5%', containLabel: true },
      xAxis: { type: 'value', axisLabel: { color: '#9ca3af' } },
      yAxis: {
        type: 'category',
        data: sorted.map(f => f.feature.replace(/_/g, ' ')),
        axisLabel: { color: '#9ca3af', fontSize: 11 }
      },
      series: [
        {
          name: 'Importance (%)',
          type: 'bar',
          data: sorted.map(f => f.percentage ?? f.importance),
          itemStyle: {
            color: {
              type: 'linear', x: 0, y: 0, x2: 1, y2: 0,
              colorStops: [{ offset: 0, color: '#4338ca' }, { offset: 1, color: '#818cf8' }]
            },
            borderRadius: [0, 4, 4, 0]
          }
        }
      ]
    };
  };

  // 2. Actual vs Predicted Scatter Option (Regression)
  const getActualVsPredictedOption = () => {
    if (!modelResult?.actual_vs_predicted?.length) return null;
    const pts = modelResult.actual_vs_predicted.map(p => [p.actual, p.predicted]);
    const minVal = Math.min(...modelResult.actual_vs_predicted.map(p => Math.min(p.actual, p.predicted)));
    const maxVal = Math.max(...modelResult.actual_vs_predicted.map(p => Math.max(p.actual, p.predicted)));

    return {
      tooltip: {
        trigger: 'item',
        formatter: (params: any) => `Actual: ${params.value[0]}<br/>Predicted: ${params.value[1]}`
      },
      grid: { left: '4%', right: '6%', bottom: '10%', top: '10%', containLabel: true },
      xAxis: { type: 'value', name: 'Actual Target', axisLabel: { color: '#9ca3af' } },
      yAxis: { type: 'value', name: 'Predicted', axisLabel: { color: '#9ca3af' } },
      series: [
        {
          type: 'scatter',
          symbolSize: 10,
          data: pts,
          itemStyle: { color: '#38bdf8' }
        },
        {
          name: 'Ideal 45° Line',
          type: 'line',
          data: [[minVal, minVal], [maxVal, maxVal]],
          lineStyle: { type: 'dashed', color: '#6366f1', width: 2 },
          symbol: 'none'
        }
      ]
    };
  };

  // 3. Target Distribution Option
  const getTargetDistributionOption = () => {
    if (!modelResult?.target_distribution) return null;
    const dist = modelResult.target_distribution;

    return {
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: '3%', right: '4%', bottom: '15%', top: '8%', containLabel: true },
      xAxis: {
        type: 'category',
        data: dist.labels,
        axisLabel: { rotate: 30, color: '#9ca3af', fontSize: 10 }
      },
      yAxis: { type: 'value', axisLabel: { color: '#9ca3af' } },
      series: [
        {
          name: 'Count / Frequency',
          type: 'bar',
          data: dist.values,
          itemStyle: {
            color: {
              type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [{ offset: 0, color: '#10b981' }, { offset: 1, color: '#047857' }]
            },
            borderRadius: [4, 4, 0, 0]
          }
        }
      ]
    };
  };

  // 4. Forecast Timeline Horizon Option
  const getForecastOption = () => {
    if (!modelResult?.forecast_data?.length) return null;
    const periods = modelResult.forecast_data.map(d => d.period);
    const actuals = modelResult.forecast_data.map(d => d.actual ?? '-');
    const forecasts = modelResult.forecast_data.map(d => d.forecast ?? '-');

    return {
      tooltip: { trigger: 'axis' },
      legend: { data: ['Historical Actuals', 'ML Forecast Horizon'], textStyle: { color: '#9ca3af' } },
      grid: { left: '3%', right: '4%', bottom: '12%', containLabel: true },
      xAxis: { type: 'category', data: periods, axisLabel: { color: '#9ca3af' } },
      yAxis: { type: 'value', axisLabel: { color: '#9ca3af' } },
      series: [
        {
          name: 'Historical Actuals',
          type: 'line',
          data: actuals,
          itemStyle: { color: '#38bdf8' },
          connectNulls: false
        },
        {
          name: 'ML Forecast Horizon',
          type: 'line',
          data: forecasts,
          itemStyle: { color: '#f59e0b' },
          lineStyle: { type: 'dashed', width: 3 },
          connectNulls: true
        }
      ]
    };
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-8 animate-fadeIn">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-xl font-bold text-white tracking-tight">
              Predictive Analytics & AutoML Studio
            </h1>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 font-medium">
              Flexible AI Modeler
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Dynamic task detection, multi-algorithm competition leaderboard, diagnostic visual curve analysis, and interactive What-If scenario simulation.
          </p>
        </div>
      </div>

      {/* Model Training Configuration Card */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl">
        <h2 className="text-sm font-semibold text-white mb-4 flex items-center space-x-2">
          <Sliders className="w-4 h-4 text-indigo-400" />
          <span>Automated Model Pipeline Setup</span>
        </h2>

        {trainError && (
          <div className="mb-4 p-3 rounded-lg bg-rose-950/40 border border-rose-800/60 text-xs text-rose-300">
            {trainError}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-2">
          {/* Task Type */}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">
              Predictive Task Type
            </label>
            <select
              value={taskType}
              onChange={(e) => setTaskType(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="auto">Auto-Detect Optimal Task</option>
              <option value="regression">Regression (Continuous Numeric)</option>
              <option value="classification">Classification (Discrete / Categorical)</option>
              <option value="forecasting">Time-Series Chronological Forecast</option>
              <option value="clustering">Clustering (K-Means Segmentation)</option>
            </select>
          </div>

          {/* Target Column */}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">
              Target Variable (Objective)
            </label>
            <select
              value={targetColumn}
              onChange={(e) => setTargetColumn(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">Auto-Select Primary Target</option>
              {profile.columns.map((c) => (
                <option key={c.name} value={c.name}>
                  {c.name} ({c.semantic_type} &bull; {c.data_type})
                </option>
              ))}
            </select>
          </div>

          {/* Train Button */}
          <div className="flex items-end">
            <button
              onClick={handleTrain}
              disabled={isTraining}
              className="w-full flex items-center justify-center space-x-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold px-4 py-2.5 rounded-lg transition shadow-md shadow-indigo-600/30"
            >
              {isTraining ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Evaluating Pipelines & Models...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  <span>Train & Compare Models</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Trained Model Results Section */}
      {modelResult && (
        <div className="space-y-8 animate-fadeIn">
          
          {/* Summary & Metrics */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800 gap-2 mb-5">
              <div>
                <div className="flex items-center space-x-2">
                  <h3 className="text-base font-bold text-white flex items-center space-x-2">
                    <Award className="w-5 h-5 text-amber-400" />
                    <span>Best Model: {modelResult.algorithm_name}</span>
                  </h3>
                  <span className="text-[11px] font-semibold uppercase px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/30">
                    {modelResult.task_type}
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-1">{modelResult.summary}</p>
              </div>
              <span className="text-[11px] font-mono text-slate-500">ID: {modelResult.model_id}</span>
            </div>

            {/* Performance KPI Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {Object.entries(modelResult.metrics)
                .filter(([k]) => !['classes', 'cluster_distribution'].includes(k))
                .map(([metricKey, metricVal]) => (
                  <div key={metricKey} className="bg-slate-800/60 p-4 rounded-xl border border-slate-700/60">
                    <span className="text-[10px] font-bold uppercase text-slate-400 tracking-wider block mb-1">
                      {metricKey.replace(/_/g, ' ')}
                    </span>
                    <span className="text-xl font-extrabold text-white">
                      {typeof metricVal === 'number' ? metricVal.toLocaleString() : String(metricVal)}
                    </span>
                  </div>
                ))}
            </div>
          </div>

          {/* Diagnostic Visuals Hub */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl">
            {/* Visual Tabs */}
            <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-5">
              <div className="flex space-x-2">
                {modelResult.model_leaderboard && modelResult.model_leaderboard.length > 0 && (
                  <button
                    onClick={() => setActiveDiagTab('leaderboard')}
                    className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition ${
                      activeDiagTab === 'leaderboard'
                        ? 'bg-indigo-600 text-white'
                        : 'text-slate-400 hover:text-white bg-slate-800'
                    }`}
                  >
                    Algorithm Leaderboard
                  </button>
                )}
                {modelResult.actual_vs_predicted && (
                  <button
                    onClick={() => setActiveDiagTab('fit')}
                    className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition ${
                      activeDiagTab === 'fit'
                        ? 'bg-indigo-600 text-white'
                        : 'text-slate-400 hover:text-white bg-slate-800'
                    }`}
                  >
                    Actual vs Predicted Fit
                  </button>
                )}
                {modelResult.feature_importance.length > 0 && (
                  <button
                    onClick={() => setActiveDiagTab('features')}
                    className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition ${
                      activeDiagTab === 'features'
                        ? 'bg-indigo-600 text-white'
                        : 'text-slate-400 hover:text-white bg-slate-800'
                    }`}
                  >
                    Feature Importance
                  </button>
                )}
                {modelResult.target_distribution && (
                  <button
                    onClick={() => setActiveDiagTab('target')}
                    className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition ${
                      activeDiagTab === 'target'
                        ? 'bg-indigo-600 text-white'
                        : 'text-slate-400 hover:text-white bg-slate-800'
                    }`}
                  >
                    Target Distribution
                  </button>
                )}
              </div>
            </div>

            {/* Tab 1: Algorithm Leaderboard */}
            {activeDiagTab === 'leaderboard' && modelResult.model_leaderboard && (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="bg-slate-800/80 text-slate-400 uppercase text-[10px] border-b border-slate-700">
                    <tr>
                      <th className="px-4 py-3 font-semibold">Algorithm Candidate</th>
                      <th className="px-4 py-3 font-semibold">Primary Metric</th>
                      <th className="px-4 py-3 font-semibold">Score</th>
                      <th className="px-4 py-3 font-semibold">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {modelResult.model_leaderboard.map((item, idx) => (
                      <tr key={idx} className={item.is_best ? 'bg-indigo-950/30' : ''}>
                        <td className="px-4 py-3 font-bold text-white flex items-center space-x-2">
                          {item.is_best && <Award className="w-4 h-4 text-amber-400" />}
                          <span>{item.algorithm}</span>
                        </td>
                        <td className="px-4 py-3 text-slate-400">{item.primary_metric}</td>
                        <td className="px-4 py-3 font-mono font-bold text-indigo-300">
                          {item.score}
                        </td>
                        <td className="px-4 py-3">
                          {item.is_best ? (
                            <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                              Top Performer
                            </span>
                          ) : (
                            <span className="text-[10px] text-slate-500">Evaluated</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Tab 2: Actual vs Predicted Fit */}
            {activeDiagTab === 'fit' && modelResult.actual_vs_predicted && (
              <div>
                <p className="text-xs text-slate-400 mb-3">
                  Scatter comparison of verified test values vs predicted values. Points close to the dashed 45° line represent high model fidelity.
                </p>
                <EChartsRenderer option={getActualVsPredictedOption()} height={320} />
              </div>
            )}

            {/* Tab 3: Feature Importance */}
            {activeDiagTab === 'features' && modelResult.feature_importance.length > 0 && (
              <div>
                <p className="text-xs text-slate-400 mb-3">
                  Ranked percentage impact of attributes explaining variance in '{modelResult.target_column}'.
                </p>
                <EChartsRenderer option={getFeatureImportanceOption()} height={320} />
              </div>
            )}

            {/* Tab 4: Target Distribution */}
            {activeDiagTab === 'target' && modelResult.target_distribution && (
              <div>
                <p className="text-xs text-slate-400 mb-3">
                  Frequency distribution of target variable '{modelResult.target_column}' across dataset rows.
                </p>
                <EChartsRenderer option={getTargetDistributionOption()} height={320} />
              </div>
            )}

            {/* If forecasting, render forecast horizon */}
            {modelResult.forecast_data && (
              <div className="mt-6 pt-6 border-t border-slate-800">
                <h4 className="text-xs font-bold uppercase tracking-wider text-amber-400 mb-3">
                  Time-Series Historical & Forward Forecast Trajectory
                </h4>
                <EChartsRenderer option={getForecastOption()} height={300} />
              </div>
            )}
          </div>

          {/* Interactive What-If Scenario Simulator with Dynamic Inputs */}
          <div className="bg-slate-900/90 border border-indigo-500/30 rounded-2xl p-6 shadow-2xl">
            <div className="flex items-center space-x-2 mb-2">
              <Sparkles className="w-4 h-4 text-indigo-400" />
              <h3 className="text-sm font-bold text-white">
                Interactive "What-If" Scenario Simulator
              </h3>
            </div>
            <p className="text-xs text-slate-400 mb-6">
              Adjust numerical sliders or categorical dropdowns below to generate real-time predictive inference.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 mb-6">
              {modelResult.features_used.slice(0, 9).map((f) => {
                const meta = modelResult.feature_meta?.[f] || {};
                const isNumeric = meta.type === 'numeric';

                return (
                  <div key={f} className="bg-slate-800/40 p-3.5 rounded-xl border border-slate-800">
                    <div className="flex items-center justify-between text-xs mb-1.5">
                      <span className="font-semibold text-slate-200 truncate">
                        {f.replace(/_/g, ' ')}
                      </span>
                      {isNumeric && (
                        <span className="font-mono text-indigo-300 font-bold text-[11px]">
                          {whatIfInputs[f] ?? meta.median}
                        </span>
                      )}
                    </div>

                    {isNumeric ? (
                      <div className="space-y-1.5">
                        <input
                          type="range"
                          min={meta.min ?? 0}
                          max={meta.max ?? 100}
                          step={(meta.max - meta.min) > 10 ? 1 : 0.1}
                          value={whatIfInputs[f] ?? meta.median ?? 0}
                          onChange={(e) =>
                            setWhatIfInputs({ ...whatIfInputs, [f]: parseFloat(e.target.value) })
                          }
                          className="w-full accent-indigo-500 cursor-pointer h-1.5 bg-slate-700 rounded-lg"
                        />
                        <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                          <span>{meta.min}</span>
                          <span>mid: {meta.median}</span>
                          <span>{meta.max}</span>
                        </div>
                      </div>
                    ) : (
                      <select
                        value={whatIfInputs[f] ?? ''}
                        onChange={(e) =>
                          setWhatIfInputs({ ...whatIfInputs, [f]: e.target.value })
                        }
                        className="w-full bg-slate-800 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                      >
                        {meta.categories ? (
                          meta.categories.map((c: string) => (
                            <option key={c} value={c}>{c}</option>
                          ))
                        ) : (
                          <option value={whatIfInputs[f] ?? ''}>{whatIfInputs[f] ?? 'Default'}</option>
                        )}
                      </select>
                    )}
                  </div>
                );
              })}
            </div>

            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-4 border-t border-slate-800">
              <button
                onClick={handlePredict}
                disabled={isPredicting}
                className="flex items-center space-x-2 bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white text-xs font-semibold px-5 py-2.5 rounded-xl shadow-lg shadow-indigo-600/30 transition active:scale-95"
              >
                {isPredicting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Evaluating Inference...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    <span>Run "What-If" Inference</span>
                  </>
                )}
              </button>

              {predictionResult && (
                <div className="flex items-baseline space-x-3 bg-indigo-950/50 border border-indigo-500/40 px-5 py-3 rounded-xl animate-scaleUp">
                  <span className="text-xs text-indigo-300 font-medium">Predicted Outcome:</span>
                  <span className="text-2xl font-black text-white">
                    {typeof predictionResult.prediction === 'number'
                      ? predictionResult.prediction.toLocaleString()
                      : String(predictionResult.prediction)}
                  </span>
                  {predictionResult.confidence && (
                    <span className="text-xs text-emerald-400 font-semibold">
                      ({(predictionResult.confidence * 100).toFixed(1)}% confidence)
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
