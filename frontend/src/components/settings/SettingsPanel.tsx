import React, { useState } from 'react';
import WindSettings from './WindSettings';
import StrategySettings from './StrategySettings';
import DisplaySettings from './DisplaySettings';
import AdvancedSettings from './AdvancedSettings';

interface SettingsPanelProps {
  isOpen: boolean;
  onClose: () => void;
  onApply: () => void;
  settings: any; // 本来は型定義を行う
  updateSettings: (category: string, key: string, value: any) => void;
}

const SettingsPanel: React.FC<SettingsPanelProps> = ({
  isOpen,
  onClose,
  onApply,
  settings,
  updateSettings,
}) => {
  const [activeTab, setActiveTab] = useState('wind');
  
  // ヘルパー関数: 設定更新
  const handleSettingChange = (category: string, key: string, value: any) => {
    updateSettings(category, key, value);
  };
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* オーバーレイ */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />
      
      {/* 設定パネル */}
      <div className="fixed inset-y-0 right-0 max-w-full flex">
        <div className="relative w-full max-w-md">
          <div className="h-full flex flex-col bg-gray-900 shadow-xl overflow-y-auto">
            <div className="p-4 border-b border-gray-700 flex justify-between items-center">
              <h2 className="text-lg font-medium text-gray-200">詳細設定</h2>
              <button 
                onClick={onClose}
                className="p-2 rounded-full hover:bg-gray-800 text-gray-400"
                aria-label="Close panel"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            {/* タブナビゲーション */}
            <div className="flex border-b border-gray-700 overflow-x-auto scrollbar-hide">
              <TabButton 
                active={activeTab === 'wind'} 
                onClick={() => setActiveTab('wind')}
                label="風向風速"
              />
              <TabButton 
                active={activeTab === 'strategy'} 
                onClick={() => setActiveTab('strategy')}
                label="戦略"
              />
              <TabButton 
                active={activeTab === 'display'} 
                onClick={() => setActiveTab('display')}
                label="表示"
              />
              <TabButton 
                active={activeTab === 'advanced'} 
                onClick={() => setActiveTab('advanced')}
                label="詳細"
              />
            </div>
            
            {/* 設定内容 */}
            <div className="flex-1 p-4 overflow-y-auto">
              {activeTab === 'wind' && (
                <WindSettings 
                  settings={settings.wind}
                  onChange={(key, value) => handleSettingChange('wind', key, value)}
                />
              )}
              
              {activeTab === 'strategy' && (
                <StrategySettings
                  settings={settings.strategy}
                  onChange={(key, value) => handleSettingChange('strategy', key, value)}
                />
              )}
              
              {activeTab === 'display' && (
                <DisplaySettings
                  settings={settings.display}
                  onChange={(key, value) => handleSettingChange('display', key, value)}
                />
              )}
              
              {activeTab === 'advanced' && (
                <AdvancedSettings
                  settings={settings.advanced}
                  onChange={(key, value) => handleSettingChange('advanced', key, value)}
                />
              )}
            </div>
            
            {/* 設定適用ボタン */}
            <div className="p-4 border-t border-gray-700 bg-gray-900">
              <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-2">
                <button 
                  onClick={onApply}
                  className="w-full py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-md transition-colors"
                >
                  設定を適用して再分析
                </button>
                <button 
                  onClick={onClose}
                  className="w-full py-2 bg-gray-700 hover:bg-gray-600 text-gray-200 font-medium rounded-md transition-colors"
                >
                  キャンセル
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// タブボタンコンポーネント
const TabButton: React.FC<{ active: boolean; onClick: () => void; label: string }> = ({
  active,
  onClick,
  label
}) => (
  <button 
    className={`flex-none px-4 py-3 text-sm font-medium whitespace-nowrap ${
      active ? 'text-blue-400 border-b-2 border-blue-400' : 'text-gray-400 hover:text-gray-300'
    }`}
    onClick={onClick}
  >
    {label}
  </button>
);

export default SettingsPanel;
