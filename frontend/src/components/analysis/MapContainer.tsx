import React, { useState, useRef, useEffect } from 'react';
import maplibregl from 'maplibre-gl';
import MapView from '@/components/map/MapView';
import TrackLayer from '@/components/map/TrackLayer';
import WindLayer from '@/components/map/WindLayer';
import StrategyPointLayer from '@/components/map/StrategyPointLayer';
import TimeSlider from '@/components/analysis/TimeSlider';
import { GpsPoint, WindDataPoint, StrategyPoint } from '@/types/gps';

interface MapContainerProps {
  gpsData: GpsPoint[];
  windData?: WindDataPoint[];
  strategyPoints?: StrategyPoint[];
  activeView: 'track' | 'wind' | 'strategy';
  mapStyle?: 'dark' | 'satellite' | 'nautical';
  colorScheme?: 'speed' | 'vmg' | 'heading';
  showLabels?: boolean;
  className?: string;
}

const MapContainer: React.FC<MapContainerProps> = ({
  gpsData,
  windData = [],
  strategyPoints = [],
  activeView = 'track',
  mapStyle = 'dark',
  colorScheme = 'speed',
  showLabels = true,
  className = '',
}) => {
  const [map, setMap] = useState<maplibregl.Map | null>(null);
  const [currentTime, setCurrentTime] = useState<number>(
    gpsData.length > 0 ? gpsData[0].timestamp : Date.now()
  );
  const [isPlaying, setIsPlaying] = useState(false);

  // データの時間範囲を計算
  const startTime = gpsData.length > 0 ? gpsData[0].timestamp : Date.now();
  const endTime = gpsData.length > 0 ? gpsData[gpsData.length - 1].timestamp : Date.now() + 3600000;

  // マップが読み込まれたときのハンドラ
  const handleMapLoaded = (mapInstance: maplibregl.Map) => {
    setMap(mapInstance);
  };

  // 時間変更ハンドラ
  const handleTimeChange = (time: number) => {
    setCurrentTime(time);
  };

  // 再生状態変更ハンドラ
  const handlePlayingChange = () => {
    setIsPlaying(!isPlaying);
  };

  // ポイントクリックハンドラ
  const handlePointClick = (point: GpsPoint) => {
    setCurrentTime(point.timestamp);
  };

  return (
    <div className={`relative w-full h-full flex flex-col ${className}`}>
      {/* 地図表示エリア */}
      <div className="flex-1 relative">
        <MapView
          style={mapStyle}
          onMapLoaded={handleMapLoaded}
          height="100%"
        >
          {map && (
            <>
              {/* 現在のビューに基づいたレイヤーを表示 */}
              {activeView === 'track' && (
                <TrackLayer
                  map={map}
                  trackData={gpsData}
                  colorScheme={colorScheme}
                  selectedTime={currentTime}
                  onPointClick={handlePointClick}
                />
              )}
              
              {activeView === 'wind' && windData.length > 0 && (
                <>
                  <TrackLayer
                    map={map}
                    trackData={gpsData}
                    colorScheme={colorScheme}
                    selectedTime={currentTime}
                    onPointClick={handlePointClick}
                    lineWidth={2}
                    showPoints={false}
                    fitBounds={false}
                  />
                  <WindLayer
                    map={map}
                    windPoints={windData}
                    selectedTime={currentTime}
                    timeWindow={300000} // 5分のウィンドウ
                    showHeatmap={true}
                    heatmapOpacity={0.6}
                  />
                </>
              )}
              
              {activeView === 'strategy' && strategyPoints.length > 0 && (
                <>
                  <TrackLayer
                    map={map}
                    trackData={gpsData}
                    colorScheme={colorScheme}
                    selectedTime={currentTime}
                    onPointClick={handlePointClick}
                    lineWidth={2}
                    showPoints={false}
                    fitBounds={false}
                  />
                  <StrategyPointLayer
                    map={map}
                    strategyPoints={strategyPoints}
                    showLabels={showLabels}
                    selectedTime={currentTime}
                    timeWindow={600000} // 10分のウィンドウ
                  />
                </>
              )}
            </>
          )}
        </MapView>
      </div>
      
      {/* タイムスライダー */}
      <div className="bg-gray-900 bg-opacity-90 backdrop-filter backdrop-blur-sm p-4 shadow-lg">
        <TimeSlider
          startTime={startTime}
          endTime={endTime}
          currentTime={currentTime}
          onTimeChange={handleTimeChange}
          isPlaying={isPlaying}
          onPlayToggle={handlePlayingChange}
        />
      </div>
    </div>
  );
};

export default MapContainer;