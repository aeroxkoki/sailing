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
} from 'recharts';

export interface WindDataPoint {
  timestamp: number;
  direction: number; // in degrees
  speed: number; // in knots
  gust?: number; // optional gust speed
}

interface WindChartProps {
  data: WindDataPoint[];
  height?: number | string;
  width?: number | string;
  showDirection?: boolean;
  showSpeed?: boolean;
  showGust?: boolean;
  directionColor?: string;
  speedColor?: string;
  gustColor?: string;
  selectedTime?: number;
  onTimeSelect?: (timestamp: number) => void;
  zoomRange?: [number, number]; // [startTime, endTime]
  className?: string;
}

const WindChart: React.FC<WindChartProps> = ({
  data,
  height = 300,
  width = '100%',
  showDirection = true,
  showSpeed = true,
  showGust = true,
  directionColor = '#8884d8',
  speedColor = '#82ca9d',
  gustColor = '#ff7300',
  selectedTime,
  onTimeSelect,
  zoomRange,
  className = '',
}) => {
  const [hoveredTime, setHoveredTime] = useState<number | null>(null);

  // Process data to handle direction wrapping (0/360 degrees)
  const processedData = data.map((point, index, arr) => {
    let { direction, speed, gust, timestamp } = point;
    
    // Handle direction wrapping for smoother chart
    if (index > 0) {
      const prevDirection = arr[index - 1].direction;
      if (Math.abs(direction - prevDirection) > 180) {
        // Adjust for wrapping
        if (direction > prevDirection) {
          direction -= 360;
        } else {
          direction += 360;
        }
      }
    }
    
    return {
      timestamp,
      direction,
      speed,
      gust,
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
          <p className="font-bold">{data.time}</p>
          {showDirection && (
            <p className="text-gray-700">
              風向: <span className="font-medium">{Math.round(data.direction % 360)}°</span>
            </p>
          )}
          {showSpeed && (
            <p className="text-gray-700">
              風速: <span className="font-medium">{data.speed.toFixed(1)} kts</span>
            </p>
          )}
          {showGust && data.gust !== undefined && (
            <p className="text-gray-700">
              突風: <span className="font-medium">{data.gust.toFixed(1)} kts</span>
            </p>
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

  return (
    <div className={`bg-white p-4 rounded-lg shadow ${className}`}>
      <h3 className="text-lg font-semibold mb-4">風向風速チャート</h3>
      <ResponsiveContainer width={width} height={height}>
        <LineChart
          data={chartData}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
          onClick={handleClick}
          onMouseMove={handleMouseMove}
          onMouseLeave={handleMouseLeave}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="time" 
            scale="time"
            tickFormatter={(time) => time}
          />
          
          {/* Direction Y-axis */}
          {showDirection && (
            <YAxis
              yAxisId="direction"
              domain={[0, 360]}
              tickFormatter={(value) => `${value}°`}
              orientation="left"
            />
          )}
          
          {/* Speed Y-axis */}
          {(showSpeed || showGust) && (
            <YAxis
              yAxisId="speed"
              domain={[0, 'auto']}
              tickFormatter={(value) => `${value} kts`}
              orientation="right"
            />
          )}
          
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          
          {showDirection && (
            <Line
              yAxisId="direction"
              type="monotone"
              dataKey="direction"
              name="風向"
              stroke={directionColor}
              dot={false}
              activeDot={{ r: 8 }}
            />
          )}
          
          {showSpeed && (
            <Line
              yAxisId="speed"
              type="monotone"
              dataKey="speed"
              name="風速"
              stroke={speedColor}
              dot={false}
            />
          )}
          
          {showGust && (
            <Line
              yAxisId="speed"
              type="monotone"
              dataKey="gust"
              name="突風"
              stroke={gustColor}
              strokeDasharray="5 5"
              dot={false}
            />
          )}
          
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
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default WindChart;