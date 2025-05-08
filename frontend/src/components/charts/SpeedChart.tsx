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
  ReferenceArea,
} from 'recharts';

export interface SpeedDataPoint {
  timestamp: number;
  speed: number; // in knots
  targetSpeed?: number; // optional target speed
  vmg?: number; // optional velocity made good
  heading?: number; // optional heading
}

export interface StrategyMark {
  timestamp: number;
  type: 'tack' | 'gybe' | 'mark' | 'start' | 'finish' | 'custom';
  label?: string;
}

interface SpeedChartProps {
  data: SpeedDataPoint[];
  height?: number | string;
  width?: number | string;
  showTarget?: boolean;
  showVMG?: boolean;
  showHeading?: boolean;
  speedColor?: string;
  targetColor?: string;
  vmgColor?: string;
  strategyMarks?: StrategyMark[];
  selectedTime?: number;
  onTimeSelect?: (timestamp: number) => void;
  zoomRange?: [number, number]; // [startTime, endTime]
  onTimeRangeChange?: (range: [number, number]) => void;
  className?: string;
}

const SpeedChart: React.FC<SpeedChartProps> = ({
  data,
  height = 300,
  width = '100%',
  showTarget = true,
  showVMG = true,
  showHeading = false,
  speedColor = '#82ca9d',
  targetColor = '#8884d8',
  vmgColor = '#ff7300',
  strategyMarks = [],
  selectedTime,
  onTimeSelect,
  zoomRange,
  onTimeRangeChange,
  className = '',
}) => {
  const [hoveredTime, setHoveredTime] = useState<number | null>(null);
  const [startBrush, setStartBrush] = useState<number | null>(null);
  const [endBrush, setEndBrush] = useState<number | null>(null);

  // Process data to add formatted time
  const processedData = data.map((point) => {
    const { timestamp, speed, targetSpeed, vmg, heading } = point;
    
    return {
      timestamp,
      speed,
      targetSpeed,
      vmg,
      heading,
      // Format the timestamp for display
      time: new Date(timestamp).toLocaleTimeString('ja-JP', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      }),
    };
  });

  // Filter data based on zoom range if provided
  const chartData = zoomRange
    ? processedData.filter(
        (point) => point.timestamp >= zoomRange[0] && point.timestamp <= zoomRange[1]
      )
    : processedData;

  // Find strategy marks within range
  const visibleMarks = strategyMarks.filter((mark) => {
    if (zoomRange) {
      return mark.timestamp >= zoomRange[0] && mark.timestamp <= zoomRange[1];
    }
    return true;
  });

  // Custom tooltip component
  const CustomTooltip = ({
    active,
    payload,
    label,
  }: TooltipProps<number, string>) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      
      // Find if there's a strategy mark at this time
      const mark = visibleMarks.find((m) => {
        const dataTime = new Date(data.timestamp).toLocaleTimeString('ja-JP', {
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
        });
        const markTime = new Date(m.timestamp).toLocaleTimeString('ja-JP', {
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
        });
        return dataTime === markTime;
      });
      
      return (
        <div className="bg-white p-2 border border-gray-200 shadow-md rounded text-sm">
          <p className="font-bold">{data.time}</p>
          <p className="text-gray-700">
            速度: <span className="font-medium">{data.speed.toFixed(1)} kts</span>
          </p>
          {showTarget && data.targetSpeed !== undefined && (
            <p className="text-gray-700">
              目標: <span className="font-medium">{data.targetSpeed.toFixed(1)} kts</span>
            </p>
          )}
          {showVMG && data.vmg !== undefined && (
            <p className="text-gray-700">
              VMG: <span className="font-medium">{data.vmg.toFixed(1)} kts</span>
            </p>
          )}
          {showHeading && data.heading !== undefined && (
            <p className="text-gray-700">
              方位: <span className="font-medium">{Math.round(data.heading)}°</span>
            </p>
          )}
          {mark && (
            <p className="mt-1 text-blue-700 font-medium">
              {getMarkLabel(mark.type)}{mark.label ? `: ${mark.label}` : ''}
            </p>
          )}
        </div>
      );
    }
    return null;
  };

  const getMarkLabel = (type: StrategyMark['type']) => {
    switch (type) {
      case 'tack': return 'タック';
      case 'gybe': return 'ジャイブ';
      case 'mark': return 'マーク';
      case 'start': return 'スタート';
      case 'finish': return 'フィニッシュ';
      case 'custom': return 'ポイント';
      default: return 'ポイント';
    }
  };

  const handleClick = (data: any) => {
    if (onTimeSelect && data && data.activePayload && data.activePayload.length > 0) {
      onTimeSelect(data.activePayload[0].payload.timestamp);
    }
  };

  const handleMouseMove = (data: any) => {
    if (data && data.activePayload && data.activePayload.length > 0) {
      setHoveredTime(data.activePayload[0].payload.timestamp);
      
      // ブラシの開始点が設定されていれば、終了点を更新
      if (startBrush !== null && data.activePayload[0].payload.timestamp !== startBrush) {
        setEndBrush(data.activePayload[0].payload.timestamp);
      }
    } else {
      setHoveredTime(null);
    }
  };

  const handleMouseLeave = () => {
    setHoveredTime(null);
  };

  // ブラシ（選択領域）の開始
  const handleMouseDown = (data: any) => {
    if (!data || !data.activeLabel) return;
    
    const point = chartData.find(p => p.time === data.activeLabel);
    if (point) {
      setStartBrush(point.timestamp);
      setEndBrush(null);
    }
  };

  // ブラシ（選択領域）の適用
  const handleMouseUp = () => {
    if (startBrush !== null && endBrush !== null && onTimeRangeChange) {
      // 開始時間と終了時間を順序正しく設定
      const startTime = Math.min(startBrush, endBrush);
      const endTime = Math.max(startBrush, endBrush);
      
      // 親コンポーネントに範囲変更を通知
      onTimeRangeChange([startTime, endTime]);
      
      // ブラシをリセット
      setStartBrush(null);
      setEndBrush(null);
    }
  };

  // Get mark color based on type
  const getMarkColor = (type: StrategyMark['type']) => {
    switch (type) {
      case 'tack': return '#4CAF50';
      case 'gybe': return '#2196F3';
      case 'mark': return '#F44336';
      case 'start': return '#9C27B0';
      case 'finish': return '#FF9800';
      case 'custom': return '#795548';
      default: return '#000000';
    }
  };

  return (
    <div className={`bg-white p-4 rounded-lg shadow ${className}`}>
      <h3 className="text-lg font-semibold mb-4">速度プロファイル</h3>
      <ResponsiveContainer width={width} height={height}>
        <LineChart
          data={chartData}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
          onClick={handleClick}
          onMouseMove={handleMouseMove}
          onMouseLeave={handleMouseLeave}
          onMouseDown={handleMouseDown}
          onMouseUp={handleMouseUp}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="time" 
            scale="time"
            tickFormatter={(time) => time}
          />
          
          <YAxis
            domain={[0, 'auto']}
            tickFormatter={(value) => `${value} kts`}
          />
          
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          
          <Line
            type="monotone"
            dataKey="speed"
            name="速度"
            stroke={speedColor}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 8 }}
          />
          
          {showTarget && (
            <Line
              type="monotone"
              dataKey="targetSpeed"
              name="目標速度"
              stroke={targetColor}
              strokeDasharray="5 5"
              dot={false}
            />
          )}
          
          {showVMG && (
            <Line
              type="monotone"
              dataKey="vmg"
              name="VMG"
              stroke={vmgColor}
              strokeWidth={1.5}
              dot={false}
            />
          )}
          
          {/* Strategy marks */}
          {visibleMarks.map((mark, index) => {
            const time = new Date(mark.timestamp).toLocaleTimeString('ja-JP', {
              hour: '2-digit',
              minute: '2-digit',
              second: '2-digit',
            });
            
            return (
              <ReferenceLine
                key={`mark-${index}`}
                x={time}
                stroke={getMarkColor(mark.type)}
                strokeWidth={2}
                label={{
                  value: getMarkLabel(mark.type),
                  position: 'top',
                  fill: getMarkColor(mark.type),
                  fontSize: 10,
                }}
              />
            );
          })}
          
          {/* Add reference line for selected time */}
          {selectedTime && (
            <ReferenceLine
              x={chartData.find((d) => d.timestamp === selectedTime)?.time}
              stroke="#ff0000"
              strokeWidth={2}
            />
          )}
          
          {/* Add reference line for hovered time */}
          {hoveredTime && hoveredTime !== selectedTime && (
            <ReferenceLine
              x={chartData.find((d) => d.timestamp === hoveredTime)?.time}
              stroke="#666666"
              strokeWidth={1}
              strokeDasharray="3 3"
            />
          )}
          
          {/* Add reference area for brush selection */}
          {startBrush && endBrush && (
            <ReferenceArea
              x1={chartData.find((d) => d.timestamp === Math.min(startBrush, endBrush))?.time}
              x2={chartData.find((d) => d.timestamp === Math.max(startBrush, endBrush))?.time}
              strokeOpacity={0.3}
              stroke="#2196F3"
              fill="#2196F3"
              fillOpacity={0.2}
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default SpeedChart;