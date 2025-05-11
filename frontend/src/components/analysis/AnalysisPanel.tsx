import React, { useState } from 'react';
import TimeSlider from './TimeSlider';
import MetricCard from './MetricCard';
import LayerControl from '../map/LayerControl';
import ExportPanel from './ExportPanel';
import DetailView from './DetailView';
import { formatWindDirection, formatWindSpeed } from '../../utils/formatters';

interface AnalysisPanelProps {
  activeView: 'track' | 'wind' | 'strategy';
  onViewChange: (view: 'track' | 'wind' | 'strategy') => void;
  onSettingsOpen: () => void;
  data: any; // 本来は型定義を行う
  className?: string;
  onLayerToggle?: (id: string, isVisible: boolean) => void;
  layers?: Array<{
    id: string;
    label: string;
    isVisible: boolean;
    icon?: React.ReactNode;
    color?: string;
  }>;
  onTimeChange?: (time: number) => void;
  playing?: boolean;
  onPlayingChange?: React.Dispatch<React.SetStateAction<boolean>>;
}

const AnalysisPanel: React.FC<AnalysisPanelProps> = ({
  activeView,
  onViewChange,
  onSettingsOpen,
  data,
  className = '',
  onLayerToggle,
  layers = [],
  onTimeChange,
  playing,
  onPlayingChange,
}) => {
  // playingとonPlayingChangeが渡されている場合はそれを使用、なければ内部状態を使用
  const [internalPlaying, setInternalPlaying] = useState(false);
  const isPlaying = playing !== undefined ? playing : internalPlaying;
  const setIsPlaying = onPlayingChange || setInternalPlaying;
  
  const [isPanelExpanded, setIsPanelExpanded] = useState(false);
  const [isExportOpen, setIsExportOpen] = useState(false);
  const [isDetailViewOpen, setIsDetailViewOpen] = useState(false);
  
  // 再生/停止の切り替え
  const handlePlayToggle = () => {
    setIsPlaying(!isPlaying);
  };
  
  // 時間変更ハンドラ
  const handleTimeChange = (time: number) => {
    // 親コンポーネントに通知
    if (onTimeChange) {
      onTimeChange(time);
    }
  };
  
  // パネル展開/折りたたみの切り替え
  const togglePanel = () => {
    setIsPanelExpanded(!isPanelExpanded);
  };
  
  return (
    <div className={`fixed bottom-0 left-0 right-0 bg-gray-900 bg-opacity-80 backdrop-filter backdrop-blur-sm z-10 transition-all duration-300 ${className}`}>
      {/* 展開/折りたたみハンドル（モバイル用） */}
      <div 
        className="absolute -top-6 left-1/2 transform -translate-x-1/2 md:hidden"
        onClick={togglePanel}
      >
        <div className="bg-gray-900 bg-opacity-80 backdrop-filter backdrop-blur-sm rounded-t-md px-4 py-1">
          <svg 
            xmlns="http://www.w3.org/2000/svg" 
            className={`h-5 w-5 text-gray-400 transition-transform ${isPanelExpanded ? 'rotate-180' : ''}`} 
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>
      
      {/* タイムスライダー */}
      <div className="p-4">
        <TimeSlider
          startTime={data.startTime || Date.now() - 3600000}
          endTime={data.endTime || Date.now()}
          currentTime={data.currentTime || Date.now()}
          onTimeChange={handleTimeChange}
          isPlaying={isPlaying}
          onPlayToggle={handlePlayToggle}
        />
      </div>
      
      {/* データダッシュボード */}
      <div className={`px-4 pb-4 transition-all duration-300 overflow-hidden ${isPanelExpanded ? 'max-h-96' : 'max-h-0 md:max-h-96'}`}>
        {/* ビュー切り替えタブ（モバイルでは横スクロール） */}
        <div className="mb-4 overflow-x-auto md:overflow-visible">
          <div className="flex space-x-2 min-w-max md:min-w-0">
            <button
              onClick={() => onViewChange('track')}
              className={`px-4 py-2 rounded-md text-sm font-medium ${
                activeView === 'track' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              航跡
            </button>
            <button
              onClick={() => onViewChange('wind')}
              className={`px-4 py-2 rounded-md text-sm font-medium ${
                activeView === 'wind' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              風向風速
            </button>
            <button
              onClick={() => onViewChange('strategy')}
              className={`px-4 py-2 rounded-md text-sm font-medium ${
                activeView === 'strategy' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              戦略
            </button>
            <button
              onClick={onSettingsOpen}
              className="px-4 py-2 rounded-md text-sm font-medium bg-gray-800 text-gray-400 hover:bg-gray-700"
            >
              設定
            </button>
            <button
              onClick={() => setIsExportOpen(true)}
              className="px-4 py-2 rounded-md text-sm font-medium bg-gray-800 text-gray-400 hover:bg-gray-700"
            >
              エクスポート
            </button>
            <button
              onClick={() => setIsDetailViewOpen(true)}
              className="px-4 py-2 rounded-md text-sm font-medium bg-gray-800 text-gray-400 hover:bg-gray-700"
            >
              詳細
            </button>
          </div>
        </div>
        
        {/* レイヤー制御（デスクトップ表示の場合） */}
        {layers.length > 0 && onLayerToggle && (
          <div className="hidden md:block absolute top-4 right-4 z-10">
            <LayerControl
              layers={layers}
              onLayerToggle={onLayerToggle}
              className="mb-4"
            />
          </div>
        )}
        
        {/* エクスポートパネル */}
        {isExportOpen && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="w-full max-w-md">
              <ExportPanel 
                onClose={() => setIsExportOpen(false)} 
              />
            </div>
          </div>
        )}
        
        {/* 詳細ビュー */}
        {isDetailViewOpen && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="w-full max-w-2xl max-h-[80vh] overflow-auto">
              <DetailView 
                onClose={() => setIsDetailViewOpen(false)} 
              />
            </div>
          </div>
        )}
        
        {/* メトリックカード */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
          {/* 風向風速情報 */}
          <MetricCard
            label="平均風向"
            value={formatWindDirection(data.averageWindDirection || 0)}
            icon={
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
              </svg>
            }
          />
          <MetricCard
            label="平均風速"
            value={parseFloat((data.averageWindSpeed || 0).toFixed(1))}
            unit="kts"
            color="info"
          />
          
          {/* 速度情報 */}
          <MetricCard
            label="最高速度"
            value={parseFloat((data.maxSpeed || 0).toFixed(1))}
            unit="kts"
            color="success"
          />
          <MetricCard
            label="平均速度"
            value={parseFloat((data.avgSpeed || 0).toFixed(1))}
            unit="kts"
          />
          
          {/* VMG情報 */}
          <MetricCard
            label="VMG（風上）"
            value={parseFloat((data.upwindVMG || 0).toFixed(1))}
            unit="kts"
          />
          <MetricCard
            label="VMG（風下）"
            value={parseFloat((data.downwindVMG || 0).toFixed(1))}
            unit="kts"
          />
        </div>
        
        {/* 戦略ビューの場合、追加情報 */}
        {activeView === 'strategy' && (
          <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3">
            <MetricCard
              label="タック回数"
              value={data.totalTacks || 0}
              size="sm"
            />
            <MetricCard
              label="ジャイブ回数"
              value={data.totalJibes || 0}
              size="sm"
            />
            <MetricCard
              label="総距離"
              value={parseFloat(((data.trackLength || 0) / 1000).toFixed(2))}
              unit="km"
              size="sm"
            />
            <MetricCard
              label="パフォーマンス"
              value={parseInt(((data.performanceScore || 0) * 100).toFixed(0))}
              unit="%"
              size="sm"
              color={
                (data.performanceScore || 0) > 0.8 
                  ? 'success' 
                  : (data.performanceScore || 0) > 0.6 
                    ? 'warning' 
                    : 'danger'
              }
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default AnalysisPanel;
