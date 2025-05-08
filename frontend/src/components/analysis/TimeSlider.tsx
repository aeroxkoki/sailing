import React, { useState, useEffect, useCallback } from 'react';
import { formatTime } from '../../utils/formatters';

interface TimeSliderProps {
  startTime: number;
  endTime: number;
  currentTime: number;
  onTimeChange: (time: number) => void;
  isPlaying?: boolean;
  onPlayToggle?: () => void;
  className?: string;
}

const TimeSlider: React.FC<TimeSliderProps> = ({
  startTime,
  endTime,
  currentTime,
  onTimeChange,
  isPlaying = false,
  onPlayToggle,
  className = '',
}) => {
  const [sliderValue, setSliderValue] = useState<number>(0);
  const timeRange = endTime - startTime;
  
  // Calculate percentage of time elapsed (0-100)
  const calculatePercentage = useCallback((time: number) => {
    if (timeRange <= 0) return 0;
    return ((time - startTime) / timeRange) * 100;
  }, [startTime, timeRange]);
  
  // Calculate time from percentage
  const calculateTime = useCallback((percentage: number) => {
    return Math.round(startTime + (percentage / 100) * timeRange);
  }, [startTime, timeRange]);
  
  // Update slider when currentTime changes
  useEffect(() => {
    setSliderValue(calculatePercentage(currentTime));
  }, [currentTime, calculatePercentage]);
  
  // Handle slider change
  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = parseFloat(e.target.value);
    setSliderValue(newValue);
  };
  
  // Handle slider release - update actual time
  const handleSliderRelease = () => {
    const newTime = calculateTime(sliderValue);
    onTimeChange(newTime);
  };
  
  return (
    <div className={`w-full ${className}`}>
      <div className="flex flex-col md:flex-row items-center justify-between mb-2">
        <div className="text-sm text-gray-400 mb-2 md:mb-0">
          {formatTime(new Date(currentTime))}
        </div>
        
        {onPlayToggle && (
          <div className="flex items-center space-x-2">
            <button
              className="w-8 h-8 flex items-center justify-center rounded-full bg-gray-800 hover:bg-gray-700 text-gray-300"
              onClick={onPlayToggle}
              aria-label={isPlaying ? 'Pause' : 'Play'}
            >
              {isPlaying ? (
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              ) : (
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              )}
            </button>
            
            <div className="text-xs text-gray-500">
              {isPlaying ? '再生中' : '停止中'}
            </div>
          </div>
        )}
        
        <div className="hidden md:block text-sm text-gray-400">
          {formatTime(new Date(startTime))} - {formatTime(new Date(endTime))}
        </div>
      </div>
      
      <div className="relative h-6 flex items-center">
        <input
          type="range"
          className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-600"
          min="0"
          max="100"
          step="0.1"
          value={sliderValue}
          onChange={handleSliderChange}
          onMouseUp={handleSliderRelease}
          onTouchEnd={handleSliderRelease}
        />
      </div>
      
      <div className="flex justify-between text-xs text-gray-500 mt-1 md:hidden">
        <span>{formatTime(new Date(startTime))}</span>
        <span>{formatTime(new Date(endTime))}</span>
      </div>
    </div>
  );
};

export default TimeSlider;
