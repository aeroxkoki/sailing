import React, { useState } from 'react';
import { GpsPoint, StrategyPointType } from '@/types/gps';
import { useAnalysis } from '@/context/AnalysisContext';
import SpeedChart from '@/components/charts/SpeedChart';
import WindChart from '@/components/charts/WindChart';

interface DetailViewProps {
  className?: string;
  onClose?: () => void;
}

const DetailView: React.FC<DetailViewProps> = ({ className = '', onClose }) => {
  const { data } = useAnalysis();
  const [activeTab, setActiveTab] = useState<'speed' | 'wind' | 'strategy' | 'data'>('speed');
  const [timeRange, setTimeRange] = useState<[number, number] | null>(null);

  // 選択されている時間周辺のデータのみを取得
  const getVisibleData = () => {
    if (!data.gpsData || data.gpsData.length === 0) return [];
    
    // GpsPointからSpeedDataPointへの変換
    const convertToSpeedDataPoint = (points: GpsPoint[]) => {
      return points
        .filter(point => point.speed !== undefined) // speedが存在するポイントのみフィルタリング
        .map(point => ({
          timestamp: point.timestamp,
          speed: point.speed as number, // speedが存在することを確認済み
          heading: point.heading
        }));
    };
    
    if (!timeRange) {
      // 時間範囲が指定されていない場合はすべてのデータを返す
      return convertToSpeedDataPoint(data.gpsData);
    }
    
    const [startTime, endTime] = timeRange;
    const filteredData = data.gpsData.filter(
      point => point.timestamp >= startTime && point.timestamp <= endTime
    );
    
    return convertToSpeedDataPoint(filteredData);
  };

  // 現在のポイントの詳細データを取得
  const getCurrentPointData = (): GpsPoint | null => {
    if (!data.gpsData || data.gpsData.length === 0 || !data.currentTime) return null;
    
    // 現在時間に最も近いポイントを見つける
    let closestPoint = data.gpsData[0];
    let minDiff = Math.abs(closestPoint.timestamp - data.currentTime);
    
    data.gpsData.forEach(point => {
      const diff = Math.abs(point.timestamp - data.currentTime);
      if (diff < minDiff) {
        closestPoint = point;
        minDiff = diff;
      }
    });
    
    return closestPoint;
  };

  // 選択されているポイントの風データを取得
  const getCurrentWindData = () => {
    if (!data.windData || data.windData.length === 0 || !data.currentTime) return null;
    
    // 現在時間に最も近い風データを見つける
    let closestPoint = data.windData[0];
    let minDiff = Math.abs(closestPoint.timestamp - data.currentTime);
    
    data.windData.forEach(point => {
      const diff = Math.abs(point.timestamp - data.currentTime);
      if (diff < minDiff) {
        closestPoint = point;
        minDiff = diff;
      }
    });
    
    return closestPoint;
  };

  // 戦略ポイントデータの取得
  const getStrategyPoints = () => {
    if (!data.strategyPoints || data.strategyPoints.length === 0) return [];
    
    if (!timeRange) {
      return data.strategyPoints;
    }
    
    const [startTime, endTime] = timeRange;
    return data.strategyPoints.filter(
      point => point.timestamp >= startTime && point.timestamp <= endTime
    );
  };

  // 表示データの時間範囲を更新
  const handleTimeRangeChange = (range: [number, number]) => {
    setTimeRange(range);
  };

  // 現在のポイントデータ
  const currentPoint = getCurrentPointData();
  const currentWind = getCurrentWindData();
  const strategyPoints = getStrategyPoints();

  // 時間をフォーマット
  const formatTime = (timestamp: number) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('ja-JP', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  return (
    <div className={`bg-gray-900 border border-gray-700 rounded-lg shadow-lg ${className}`}>
      <div className="flex justify-between items-center p-4 border-b border-gray-700">
        <h2 className="text-lg font-medium text-gray-200">詳細データ</h2>
        {onClose && (
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-300 focus:outline-none"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </button>
        )}
      </div>

      {/* タブナビゲーション */}
      <div className="border-b border-gray-700">
        <div className="flex">
          <button
            className={`px-4 py-2 text-sm font-medium border-b-2 ${
              activeTab === 'speed'
                ? 'text-blue-400 border-blue-400'
                : 'text-gray-400 border-transparent hover:text-gray-300'
            }`}
            onClick={() => setActiveTab('speed')}
          >
            速度
          </button>
          <button
            className={`px-4 py-2 text-sm font-medium border-b-2 ${
              activeTab === 'wind'
                ? 'text-blue-400 border-blue-400'
                : 'text-gray-400 border-transparent hover:text-gray-300'
            }`}
            onClick={() => setActiveTab('wind')}
          >
            風向風速
          </button>
          <button
            className={`px-4 py-2 text-sm font-medium border-b-2 ${
              activeTab === 'strategy'
                ? 'text-blue-400 border-blue-400'
                : 'text-gray-400 border-transparent hover:text-gray-300'
            }`}
            onClick={() => setActiveTab('strategy')}
          >
            戦略
          </button>
          <button
            className={`px-4 py-2 text-sm font-medium border-b-2 ${
              activeTab === 'data'
                ? 'text-blue-400 border-blue-400'
                : 'text-gray-400 border-transparent hover:text-gray-300'
            }`}
            onClick={() => setActiveTab('data')}
          >
            データ
          </button>
        </div>
      </div>

      {/* タブコンテンツ */}
      <div className="p-4">
        {activeTab === 'speed' && (
          <div>
            <h3 className="text-sm font-medium text-gray-400 mb-2">速度プロファイル</h3>
            <div className="h-64 mb-4">
              <SpeedChart 
                data={getVisibleData()} 
                selectedTime={data.currentTime || undefined}
                onTimeRangeChange={handleTimeRangeChange}
              />
            </div>
            
            {currentPoint && (
              <div className="mt-4 grid grid-cols-2 gap-4">
                <div className="bg-gray-800 p-3 rounded-lg">
                  <div className="text-xs text-gray-500">現在の速度</div>
                  <div className="text-lg font-semibold text-gray-200">
                    {currentPoint.speed?.toFixed(1) || 'N/A'} ノット
                  </div>
                </div>
                <div className="bg-gray-800 p-3 rounded-lg">
                  <div className="text-xs text-gray-500">方位角</div>
                  <div className="text-lg font-semibold text-gray-200">
                    {currentPoint.heading?.toFixed(0) || 'N/A'}°
                  </div>
                </div>
                <div className="bg-gray-800 p-3 rounded-lg">
                  <div className="text-xs text-gray-500">最大速度</div>
                  <div className="text-lg font-semibold text-gray-200">
                    {Math.max(...getVisibleData().map(p => p.speed)).toFixed(1)} ノット
                  </div>
                </div>
                <div className="bg-gray-800 p-3 rounded-lg">
                  <div className="text-xs text-gray-500">平均速度</div>
                  <div className="text-lg font-semibold text-gray-200">
                    {(getVisibleData().reduce((sum, p) => sum + p.speed, 0) / getVisibleData().length).toFixed(1)} ノット
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'wind' && (
          <div>
            <h3 className="text-sm font-medium text-gray-400 mb-2">風向風速データ</h3>
            <div className="h-64 mb-4">
              <WindChart 
                data={data.windData || []} 
                selectedTime={data.currentTime || undefined}
                onTimeRangeChange={handleTimeRangeChange}
              />
            </div>
            
            {currentWind && (
              <div className="mt-4 grid grid-cols-2 gap-4">
                <div className="bg-gray-800 p-3 rounded-lg">
                  <div className="text-xs text-gray-500">現在の風向</div>
                  <div className="text-lg font-semibold text-gray-200">
                    {currentWind.direction.toFixed(0)}°
                  </div>
                </div>
                <div className="bg-gray-800 p-3 rounded-lg">
                  <div className="text-xs text-gray-500">現在の風速</div>
                  <div className="text-lg font-semibold text-gray-200">
                    {currentWind.speed.toFixed(1)} ノット
                  </div>
                </div>
                <div className="bg-gray-800 p-3 rounded-lg">
                  <div className="text-xs text-gray-500">平均風向</div>
                  <div className="text-lg font-semibold text-gray-200">
                    {data.averageWindDirection.toFixed(0)}°
                  </div>
                </div>
                <div className="bg-gray-800 p-3 rounded-lg">
                  <div className="text-xs text-gray-500">平均風速</div>
                  <div className="text-lg font-semibold text-gray-200">
                    {data.averageWindSpeed.toFixed(1)} ノット
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'strategy' && (
          <div>
            <h3 className="text-sm font-medium text-gray-400 mb-2">戦略ポイント</h3>
            
            {strategyPoints.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mx-auto text-gray-600 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                </svg>
                <p>選択した時間範囲内に戦略ポイントがありません</p>
              </div>
            ) : (
              <div className="max-h-80 overflow-y-auto">
                <div className="space-y-3">
                  {strategyPoints.map((point, index) => (
                    <div 
                      key={index} 
                      className={`p-3 rounded-lg border ${
                        data.currentTime && Math.abs(point.timestamp - data.currentTime) < 5000
                          ? 'bg-blue-900 bg-opacity-30 border-blue-700'
                          : 'bg-gray-800 border-gray-700'
                      }`}
                    >
                      <div className="flex justify-between items-start">
                        <div className="flex items-center">
                          <div className={`w-2 h-2 rounded-full mr-2 ${
                            point.type === StrategyPointType.TACK ? 'bg-green-500' :
                            point.type === StrategyPointType.JIBE ? 'bg-yellow-500' :
                            point.type === StrategyPointType.MARK_ROUNDING ? 'bg-purple-500' :
                            point.type === StrategyPointType.WIND_SHIFT ? 'bg-blue-500' :
                            'bg-gray-500'
                          }`} />
                          <span className="font-medium text-gray-300 capitalize">
                            {point.type.replace('_', ' ')}
                          </span>
                        </div>
                        <span className="text-xs text-gray-500">
                          {formatTime(point.timestamp)}
                        </span>
                      </div>
                      
                      {point.details && (
                        <div className="mt-2 grid grid-cols-2 gap-2 text-sm">
                          {point.type === StrategyPointType.TACK && (
                            <>
                              <div className="text-gray-400">角度変化</div>
                              <div className="text-gray-300">{point.details.angle_change?.toFixed(0) || 'N/A'}°</div>
                              <div className="text-gray-400">速度損失</div>
                              <div className="text-gray-300">{point.details.speed_loss?.toFixed(1) || 'N/A'} ノット</div>
                            </>
                          )}
                          
                          {point.type === StrategyPointType.WIND_SHIFT && (
                            <>
                              <div className="text-gray-400">シフト量</div>
                              <div className="text-gray-300">{point.details.shift_amount?.toFixed(0) || 'N/A'}°</div>
                              <div className="text-gray-400">持続時間</div>
                              <div className="text-gray-300">{point.details.duration ? `${(point.details.duration / 60000).toFixed(1)} 分` : 'N/A'}</div>
                            </>
                          )}
                        </div>
                      )}
                      
                      {point.evaluation && (
                        <div className="mt-2 flex items-center">
                          <div className="text-xs text-gray-400 mr-2">評価:</div>
                          <div className={`text-sm font-medium ${
                            point.evaluation.score >= 0.8 ? 'text-green-400' :
                            point.evaluation.score >= 0.6 ? 'text-yellow-400' :
                            'text-red-400'
                          }`}>
                            {(point.evaluation.score * 100).toFixed(0)}%
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            <div className="mt-4 grid grid-cols-2 gap-4">
              <div className="bg-gray-800 p-3 rounded-lg">
                <div className="text-xs text-gray-500">タック回数</div>
                <div className="text-lg font-semibold text-gray-200">
                  {strategyPoints.filter(p => p.type === StrategyPointType.TACK).length}
                </div>
              </div>
              <div className="bg-gray-800 p-3 rounded-lg">
                <div className="text-xs text-gray-500">ジャイブ回数</div>
                <div className="text-lg font-semibold text-gray-200">
                  {strategyPoints.filter(p => p.type === StrategyPointType.JIBE).length}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'data' && (
          <div>
            <h3 className="text-sm font-medium text-gray-400 mb-2">生データ</h3>
            
            {currentPoint && (
              <div className="bg-gray-800 p-3 rounded-lg mb-4">
                <h4 className="text-xs font-medium text-gray-500 mb-2">現在選択されているポイント</h4>
                <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
                  <div className="text-gray-400">時間</div>
                  <div className="text-gray-300">{formatTime(currentPoint.timestamp)}</div>
                  
                  <div className="text-gray-400">緯度</div>
                  <div className="text-gray-300">{currentPoint.latitude.toFixed(6)}°</div>
                  
                  <div className="text-gray-400">経度</div>
                  <div className="text-gray-300">{currentPoint.longitude.toFixed(6)}°</div>
                  
                  <div className="text-gray-400">速度</div>
                  <div className="text-gray-300">{currentPoint.speed?.toFixed(2) || 'N/A'} ノット</div>
                  
                  <div className="text-gray-400">方位角</div>
                  <div className="text-gray-300">{currentPoint.heading?.toFixed(1) || 'N/A'}°</div>
                  
                  {currentPoint.altitude !== undefined && (
                    <>
                      <div className="text-gray-400">高度</div>
                      <div className="text-gray-300">{currentPoint.altitude.toFixed(1)} m</div>
                    </>
                  )}
                </div>
              </div>
            )}
            
            {currentWind && (
              <div className="bg-gray-800 p-3 rounded-lg">
                <h4 className="text-xs font-medium text-gray-500 mb-2">現在の風データ</h4>
                <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
                  <div className="text-gray-400">時間</div>
                  <div className="text-gray-300">{formatTime(currentWind.timestamp)}</div>
                  
                  <div className="text-gray-400">風向</div>
                  <div className="text-gray-300">{currentWind.direction.toFixed(1)}°</div>
                  
                  <div className="text-gray-400">風速</div>
                  <div className="text-gray-300">{currentWind.speed.toFixed(2)} ノット</div>
                  
                  {currentWind.confidence !== undefined && (
                    <>
                      <div className="text-gray-400">信頼度</div>
                      <div className="text-gray-300">{(currentWind.confidence * 100).toFixed(0)}%</div>
                    </>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default DetailView;
