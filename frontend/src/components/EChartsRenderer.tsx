import React, { useEffect, useRef } from 'react';
import * as echarts from 'echarts';

interface EChartsRendererProps {
  option: any;
  height?: string | number;
  className?: string;
  onPointClick?: (params: { name: string; value: any; seriesName: string }) => void;
}

export const EChartsRenderer: React.FC<EChartsRendererProps> = ({
  option,
  height = '320px',
  className = '',
  onPointClick
}) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!chartRef.current) return;

    if (!chartInstance.current) {
      chartInstance.current = echarts.init(chartRef.current, 'dark', {
        renderer: 'canvas'
      });

      if (onPointClick) {
        chartInstance.current.on('click', (params: any) => {
          onPointClick({
            name: params.name || params.seriesName || '',
            value: params.value,
            seriesName: params.seriesName || ''
          });
        });
      }
    }

    if (option) {
      const customizedOption = {
        backgroundColor: 'transparent',
        textStyle: {
          fontFamily: '-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif'
        },
        ...option
      };
      chartInstance.current.setOption(customizedOption, true);
    }

    const handleResize = () => {
      chartInstance.current?.resize();
    };

    window.addEventListener('resize', handleResize);
    const resizeObserver = new ResizeObserver(() => {
      chartInstance.current?.resize();
    });
    resizeObserver.observe(chartRef.current);

    return () => {
      window.removeEventListener('resize', handleResize);
      resizeObserver.disconnect();
    };
  }, [option, onPointClick]);

  useEffect(() => {
    return () => {
      chartInstance.current?.dispose();
      chartInstance.current = null;
    };
  }, []);

  return (
    <div
      ref={chartRef}
      style={{ width: '100%', height }}
      className={`relative ${className}`}
    />
  );
};
