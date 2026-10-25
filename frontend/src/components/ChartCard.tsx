import React, { useState } from 'react';
import {
  BarChart2,
  LineChart,
  Table as TableIcon,
  Sparkles,
  Maximize2,
  Minimize2,
  ArrowUpDown,
  Filter
} from 'lucide-react';
import { ChartSpec } from '../types';
import { EChartsRenderer } from './EChartsRenderer';

interface ChartCardProps {
  chart: ChartSpec;
  onCrossFilter?: (column: string, value: string) => void;
}

export const ChartCard: React.FC<ChartCardProps> = ({ chart, onCrossFilter }) => {
  const [activeType, setActiveType] = useState<string>(chart.chart_type);
  const [showTable, setShowTable] = useState<boolean>(false);
  const [isExpanded, setIsExpanded] = useState<boolean>(false);
  const [isSortedAsc, setIsSortedAsc] = useState<boolean>(false);

  // Dynamically adapt echarts_option
  const getRenderOption = () => {
    if (!chart.echarts_option) return null;
    const baseOpt = JSON.parse(JSON.stringify(chart.echarts_option));

    // Support sorting if category xAxis
    if (baseOpt.xAxis && baseOpt.xAxis.data && baseOpt.series && baseOpt.series[0]?.data) {
      const combined = baseOpt.xAxis.data.map((cat: string, i: number) => ({
        cat,
        val: baseOpt.series[0].data[i]
      }));

      combined.sort((a: any, b: any) =>
        isSortedAsc ? a.val - b.val : b.val - a.val
      );

      baseOpt.xAxis.data = combined.map((c: any) => c.cat);
      baseOpt.series[0].data = combined.map((c: any) => c.val);
    }

    if (activeType === 'bar' && baseOpt.series && baseOpt.series[0]) {
      baseOpt.series[0].type = 'bar';
      delete baseOpt.series[0].areaStyle;
      baseOpt.series[0].itemStyle = {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [{ offset: 0, color: '#6366f1' }, { offset: 1, color: '#4338ca' }]
        },
        borderRadius: [4, 4, 0, 0]
      };
    } else if (activeType === 'line' && baseOpt.series && baseOpt.series[0]) {
      baseOpt.series[0].type = 'line';
      baseOpt.series[0].smooth = true;
      delete baseOpt.series[0].areaStyle;
      baseOpt.series[0].itemStyle = { color: '#38bdf8' };
    } else if (activeType === 'area' && baseOpt.series && baseOpt.series[0]) {
      baseOpt.series[0].type = 'line';
      baseOpt.series[0].smooth = true;
      baseOpt.series[0].areaStyle = {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(99, 102, 241, 0.45)' },
            { offset: 1, color: 'rgba(99, 102, 241, 0.0)' }
          ]
        }
      };
      baseOpt.series[0].itemStyle = { color: '#6366f1' };
    }

    return baseOpt;
  };

  const handlePointClick = (params: { name: string; value: any; seriesName: string }) => {
    if (chart.x_axis && params.name && onCrossFilter) {
      onCrossFilter(chart.x_axis, params.name);
    }
  };

  return (
    <>
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col justify-between hover:border-slate-700/80 transition duration-150 relative">
        {/* Header with Title & Chart Type Switcher */}
        <div>
          <div className="flex items-start justify-between gap-2 mb-2">
            <div>
              <h3 className="text-sm font-semibold text-slate-100 flex items-center space-x-1.5">
                <span>{chart.title}</span>
              </h3>
              {chart.description && (
                <p className="text-xs text-slate-400 mt-0.5 line-clamp-1">
                  {chart.description}
                </p>
              )}
            </div>

            {/* Interactive Action Controls */}
            <div className="flex items-center space-x-1 bg-slate-800/80 p-0.5 rounded-lg border border-slate-700 text-slate-400">
              {/* Sort Toggle */}
              <button
                title="Toggle Sort Order"
                onClick={() => setIsSortedAsc(!isSortedAsc)}
                className="p-1 rounded hover:text-slate-200"
              >
                <ArrowUpDown className="w-3.5 h-3.5" />
              </button>

              {/* Chart Switchers */}
              <button
                title="Bar Chart"
                onClick={() => { setActiveType('bar'); setShowTable(false); }}
                className={`p-1 rounded ${activeType === 'bar' && !showTable ? 'bg-indigo-600 text-white' : 'hover:text-slate-200'}`}
              >
                <BarChart2 className="w-3.5 h-3.5" />
              </button>
              <button
                title="Line Chart"
                onClick={() => { setActiveType('line'); setShowTable(false); }}
                className={`p-1 rounded ${activeType === 'line' && !showTable ? 'bg-indigo-600 text-white' : 'hover:text-slate-200'}`}
              >
                <LineChart className="w-3.5 h-3.5" />
              </button>
              <button
                title="Data Table View"
                onClick={() => setShowTable(!showTable)}
                className={`p-1 rounded ${showTable ? 'bg-indigo-600 text-white' : 'hover:text-slate-200'}`}
              >
                <TableIcon className="w-3.5 h-3.5" />
              </button>
              <button
                title="Expand Drill-Through"
                onClick={() => setIsExpanded(true)}
                className="p-1 rounded hover:text-slate-200"
              >
                <Maximize2 className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Visual Canvas */}
          <div className="my-3 min-h-[300px] flex items-center justify-center">
            {showTable ? (
              <div className="w-full max-h-[300px] overflow-auto border border-slate-800 rounded-lg">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="bg-slate-800/80 text-slate-400 uppercase text-[10px] sticky top-0">
                    <tr>
                      {chart.data.length > 0 &&
                        Object.keys(chart.data[0]).map((key) => (
                          <th key={key} className="px-3 py-2 font-medium">
                            {key.replace(/_/g, ' ')}
                          </th>
                        ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {chart.data.map((row, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/40">
                        {Object.values(row).map((val: any, cIdx) => (
                          <td key={cIdx} className="px-3 py-2 font-mono text-[11px]">
                            {typeof val === 'number' ? val.toLocaleString() : String(val)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="w-full cursor-pointer" title="Click on any bar or point to cross-filter">
                <EChartsRenderer
                  option={getRenderOption()}
                  height={300}
                  onPointClick={handlePointClick}
                />
              </div>
            )}
          </div>
        </div>

        {/* Footer: Dynamic Automated Insight Pill */}
        {chart.insight && (
          <div className="mt-2 pt-2 border-t border-slate-800/70 flex items-center justify-between text-xs text-indigo-300 bg-indigo-950/20 px-3 py-1.5 rounded-lg border border-indigo-900/30">
            <div className="flex items-center space-x-1.5 truncate">
              <Sparkles className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
              <span className="truncate">{chart.insight}</span>
            </div>
            <span className="text-[10px] text-slate-500 uppercase tracking-wider shrink-0 pl-2">
              Click bar to filter
            </span>
          </div>
        )}
      </div>

      {/* Expanded Drill-Through Modal */}
      {isExpanded && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-6">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-5xl p-6 shadow-2xl flex flex-col max-h-[90vh]">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <div>
                <h2 className="text-base font-bold text-white">{chart.title}</h2>
                <p className="text-xs text-slate-400">{chart.description}</p>
              </div>
              <button
                onClick={() => setIsExpanded(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
              >
                <Minimize2 className="w-5 h-5" />
              </button>
            </div>

            <div className="flex-1 my-4 overflow-hidden flex flex-col items-center justify-center">
              <EChartsRenderer
                option={getRenderOption()}
                height="480px"
                onPointClick={(p) => {
                  handlePointClick(p);
                  setIsExpanded(false);
                }}
              />
            </div>

            <div className="pt-3 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
              <span>{chart.insight}</span>
              <button
                onClick={() => setIsExpanded(false)}
                className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-medium"
              >
                Close Fullscreen
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
