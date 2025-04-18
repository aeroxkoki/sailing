import React, { useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  TooltipProps,
  ReferenceLine,
  Scatter,
  ScatterChart,
  ZAxis,
  Brush,
  AreaChart,
  Area,
} from 'recharts';

export interface PerformanceDataPoint {
  timestamp: number;
  windSpeed: number; // in knots
  boatSpeed: number; // in knots
  performanceRatio?: number; // ratio of actual speed to target speed (1.0 = 100%)
  windAngle?: number; // in degrees
  heading?: number; // in degrees
  vmg?: number; // velocity made good
}

interface PerformanceChartProps {
  data: PerformanceDataPoint[];
  height?: number | string;
  width?: number | string;
  chartType?: 'line' | 'scatter' | 'area';
  xAxis?: 'time' | 'windAngle' | 'windSpeed';
  yAxis?: 'boatSpeed' | 'performanceRatio' | 'vmg';
  colorScale?: string[];
  selectedTime?: number;
  onTimeSelect?: (timestamp: number) => void;
  zoomRange?: [number, number]; // [startTime, endTime] for time chart
  className?: string;
  showBrush?: boolean;
}

const PerformanceChart: React.FC<PerformanceChartProps> = ({
  data,
  height = 300,
  width = '100%',
  chartType = 'line',
  xAxis = 'time',
  yAxis = 'boatSpeed',
  colorScale = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#0088fe'],
  selectedTime,
  onTimeSelect,
  zoomRange,
  className = '',
  showBrush = false,
}) => {
  const [hoveredTime, setHoveredTime] = useState<number | null>(null);

  // Process data to add formatted time and other derived values
  const processedData = data.map((point) => {
    const { timestamp, windSpeed, boatSpeed, performanceRatio, windAngle, heading, vmg } = point;
    
    return {
      timestamp,
      windSpeed,
      boatSpeed,
      performanceRatio: performanceRatio || (boatSpeed / (windSpeed * 0.5)), // Simple fallback calculation
      windAngle: windAngle || 0,
      heading: heading || 0,
      vmg: vmg || 0,
      // Format the timestamp for display
      time: new Date(timestamp).toLocaleTimeString('ja-JP', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      }),
    };
  });

  // Filter data based on zoom range if provided and if time-based chart
  const chartData = (xAxis === 'time' && zoomRange)
    ? processedData.filter(
        (point) => point.timestamp >= zoomRange[0] && point.timestamp <= zoomRange[1]
      )
    : processedData;

  // Get X-axis data key
  const getXAxisDataKey = () => {
    switch (xAxis) {
      case 'windAngle': return 'windAngle';
      case 'windSpeed': return 'windSpeed';
      default: return 'time';
    }
  };

  // Get Y-axis data key
  const getYAxisDataKey = () => {
    switch (yAxis) {
      case 'performanceRatio': return 'performanceRatio';
      case 'vmg': return 'vmg';
      default: return 'boatSpeed';
    }
  };

  // Get X-axis label
  const getXAxisLabel = () => {
    switch (xAxis) {
      case 'windAngle': return '風向角度 (°)';
      case 'windSpeed': return '風速 (kts)';
      default: return '時間';
    }
  };

  // Get Y-axis label
  const getYAxisLabel = () => {
    switch (yAxis) {
      case 'performanceRatio': return 'パフォーマンス比 (%)';
      case 'vmg': return 'VMG (kts)';
      default: return '艇速 (kts)';
    }
  };

  // Format Y-axis values
  const formatYAxisValue = (value: number) => {
    switch (yAxis) {
      case 'performanceRatio': return `${(value * 100).toFixed(0)}%`;
      default: return `${value.toFixed(1)} kts`;
    }
  };

  // Custom tooltip component
  const CustomTooltip = ({
    active,
    payload,
    label,
  }: TooltipProps<number, string>) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      
      return (
        <div className="bg-white p-2 border border-gray-200 shadow-md rounded text-sm">
          {xAxis === 'time' && <p className="font-bold">{data.time}</p>}
          <p className="text-gray-700">
            風速: <span className="font-medium">{data.windSpeed.toFixed(1)} kts</span>
          </p>
          <p className="text-gray-700">
            艇速: <span className="font-medium">{data.boatSpeed.toFixed(1)} kts</span>
          </p>
          {data.windAngle !== undefined && (
            <p className="text-gray-700">
              風向角度: <span className="font-medium">{Math.round(data.windAngle)}°</span>
            </p>
          )}
          {data.performanceRatio !== undefined && (
            <p className="text-gray-700">
              パフォーマンス: <span className="font-medium">{(data.performanceRatio * 100).toFixed(0)}%</span>
            </p>
          )}
          {data.vmg !== undefined && (
            <p className="text-gray-700">
              VMG: <span className="font-medium">{data.vmg.toFixed(1)} kts</span>
            </p>
          )}
          {xAxis !== 'time' && data.time && (
            <p className="text-gray-500 text-xs mt-1">{data.time}</p>
          )}
        </div>
      );
    }
    return null;
  };

  const handleClick = (data: any) => {
    if (onTimeSelect && data && data.activePayload && data.activePayload.length > 0) {
      onTimeSelect(data.activePayload[0].payload.timestamp);
    }
  };

  const handleMouseMove = (data: any) => {
    if (data && data.activePayload && data.activePayload.length > 0) {
      setHoveredTime(data.activePayload[0].payload.timestamp);
    } else {
      setHoveredTime(null);
    }
  };

  const handleMouseLeave = () => {
    setHoveredTime(null);
  };

  // Render Line Chart
  const renderLineChart = () => (
    <LineChart
      data={chartData}
      margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
      onClick={handleClick}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      <CartesianGrid strokeDasharray="3 3" />
      <XAxis 
        dataKey={getXAxisDataKey()} 
        name={getXAxisLabel()}
        tickFormatter={xAxis === 'time' ? (time) => time : undefined}
      />
      <YAxis
        tickFormatter={formatYAxisValue}
        domain={yAxis === 'performanceRatio' ? [0, 'auto'] : undefined}
      />
      <Tooltip content={<CustomTooltip />} />
      <Legend />
      <Line
        type="monotone"
        dataKey={getYAxisDataKey()}
        name={getYAxisLabel()}
        stroke={colorScale[0]}
        dot={false}
        activeDot={{ r: 8 }}
      />
      {/* Add reference line for selected time */}
      {xAxis === 'time' && selectedTime && (
        <ReferenceLine
          x={chartData.find((d) => d.timestamp === selectedTime)?.time}
          stroke="#ff0000"
          strokeWidth={2}
        />
      )}
      {/* Add reference line for hovered time */}
      {xAxis === 'time' && hoveredTime && hoveredTime !== selectedTime && (
        <ReferenceLine
          x={chartData.find((d) => d.timestamp === hoveredTime)?.time}
          stroke="#666666"
          strokeWidth={1}
          strokeDasharray="3 3"
        />
      )}
      {showBrush && xAxis === 'time' && (
        <Brush 
          dataKey="time" 
          height={30} 
          stroke={colorScale[0]}
          startIndex={chartData.length > 30 ? chartData.length - 30 : 0}
        />
      )}
    </LineChart>
  );

  // Render Scatter Chart (useful for wind angle vs boat speed plots)
  const renderScatterChart = () => (
    <ScatterChart
      margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
      onClick={handleClick}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      <CartesianGrid strokeDasharray="3 3" />
      <XAxis 
        type="number" 
        dataKey={getXAxisDataKey()} 
        name={getXAxisLabel()}
        domain={xAxis === 'windAngle' ? [0, 360] : undefined}
      />
      <YAxis 
        type="number" 
        dataKey={getYAxisDataKey()} 
        name={getYAxisLabel()}
        tickFormatter={formatYAxisValue}
      />
      <ZAxis 
        type="number" 
        dataKey="timestamp" 
        range={[50, 500]} 
      />
      <Tooltip content={<CustomTooltip />} />
      <Legend />
      <Scatter 
        name={getYAxisLabel()} 
        data={chartData} 
        fill={colorScale[0]}
      />
    </ScatterChart>
  );

  // Render Area Chart
  const renderAreaChart = () => (
    <AreaChart
      data={chartData}
      margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
      onClick={handleClick}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      <CartesianGrid strokeDasharray="3 3" />
      <XAxis 
        dataKey={getXAxisDataKey()} 
        name={getXAxisLabel()}
        tickFormatter={xAxis === 'time' ? (time) => time : undefined}
      />
      <YAxis
        tickFormatter={formatYAxisValue}
        domain={yAxis === 'performanceRatio' ? [0, 'auto'] : undefined}
      />
      <Tooltip content={<CustomTooltip />} />
      <Legend />
      <Area
        type="monotone"
        dataKey={getYAxisDataKey()}
        name={getYAxisLabel()}
        stroke={colorScale[0]}
        fill={colorScale[0]}
        fillOpacity={0.3}
      />
      {/* Add reference line for selected time */}
      {xAxis === 'time' && selectedTime && (
        <ReferenceLine
          x={chartData.find((d) => d.timestamp === selectedTime)?.time}
          stroke="#ff0000"
          strokeWidth={2}
        />
      )}
      {showBrush && xAxis === 'time' && (
        <Brush 
          dataKey="time" 
          height={30} 
          stroke={colorScale[0]}
          startIndex={chartData.length > 30 ? chartData.length - 30 : 0}
        />
      )}
    </AreaChart>
  );

  // Render chart based on type
  const renderChart = () => {
    switch (chartType) {
      case 'scatter':
        return renderScatterChart();
      case 'area':
        return renderAreaChart();
      default:
        return renderLineChart();
    }
  };

  // Get chart title based on configuration
  const getChartTitle = () => {
    let title = 'パフォーマンス分析';
    
    if (xAxis !== 'time' && yAxis !== 'boatSpeed') {
      title = `${getYAxisLabel()} vs ${getXAxisLabel()}`;
    } else if (xAxis !== 'time') {
      title = `艇速 vs ${getXAxisLabel()}`;
    } else if (yAxis !== 'boatSpeed') {
      title = `${getYAxisLabel()} 分析`;
    }
    
    return title;
  };

  return (
    <div className={`bg-white p-4 rounded-lg shadow ${className}`}>
      <h3 className="text-lg font-semibold mb-4">{getChartTitle()}</h3>
      <ResponsiveContainer width={width} height={height}>
        {renderChart()}
      </ResponsiveContainer>
    </div>
  );
};

export default PerformanceChart;