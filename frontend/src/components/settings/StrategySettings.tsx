import React from 'react';
import { StrategySettings as StrategySettingsType } from '../../types';

interface StrategySettingsProps {
  settings: StrategySettingsType;
  onChange: <K extends keyof StrategySettingsType>(key: K, value: StrategySettingsType[K]) => void;
}

// 戦略ポイントのタイプ定義
const strategyPointTypes = [
  { id: 'tack', label: 'タック' },
  { id: 'jibe', label: 'ジャイブ' },
  { id: 'mark', label: 'マーク回航' },
  { id: 'shift', label: '風向シフト' },
  { id: 'layline', label: 'レイライン' },
  { id: 'start', label: 'スタート' },
  { id: 'finish', label: 'フィニッシュ' },
];

const StrategySettings: React.FC<StrategySettingsProps> = ({ settings, onChange }) => {
  // チェックボックスの変更ハンドラ
  const handleTypeChange = (typeId: string, checked: boolean) => {
    let newTypes = [...settings.detectTypes];
    
    if (checked && !newTypes.includes(typeId)) {
      newTypes.push(typeId);
    } else if (!checked && newTypes.includes(typeId)) {
      newTypes = newTypes.filter(t => t !== typeId);
    }
    
    onChange('detectTypes', newTypes);
  };
  
  return (
    <div className="space-y-4">
      <h3 className="text-base font-medium text-gray-300 mb-3">戦略分析設定</h3>
      
      {/* 感度設定 */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-400">
          検出感度: {settings.sensitivity}%
        </label>
        <input
          type="range"
          min="0"
          max="100"
          step="5"
          value={settings.sensitivity}
          onChange={(e) => onChange('sensitivity', parseInt(e.target.value))}
          className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
        />
        <div className="flex justify-between text-xs text-gray-500">
          <span>低 (少なめに検出)</span>
          <span>高 (多めに検出)</span>
        </div>
      </div>
      
      {/* 最小信頼度 */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-400">
          最小信頼度: {settings.minConfidence}%
        </label>
        <input
          type="range"
          min="0"
          max="100"
          step="5"
          value={settings.minConfidence}
          onChange={(e) => onChange('minConfidence', parseInt(e.target.value))}
          className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
        />
        <div className="flex justify-between text-xs text-gray-500">
          <span>低 (不確かな検出も含む)</span>
          <span>高 (確実な検出のみ)</span>
        </div>
      </div>
      
      {/* 検出タイプ */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-400 mb-2">
          検出するポイントタイプ
        </label>
        <div className="grid grid-cols-2 gap-2">
          {strategyPointTypes.map(type => (
            <div key={type.id} className="flex items-center space-x-2">
              <input
                type="checkbox"
                id={`type-${type.id}`}
                checked={settings.detectTypes.includes(type.id)}
                onChange={(e) => handleTypeChange(type.id, e.target.checked)}
                className="w-4 h-4 bg-gray-800 border-gray-700 rounded text-blue-500 focus:ring-0"
              />
              <label htmlFor={`type-${type.id}`} className="text-sm text-gray-400">
                {type.label}
              </label>
            </div>
          ))}
        </div>
      </div>
      
      <div className="border-t border-gray-700 pt-4 mt-6">
        <p className="text-xs text-gray-500">
          戦略分析設定では、航跡データから重要な戦略ポイントを検出する際のパラメータを調整できます。高い感度では多くのポイントが検出されますが、誤検出の可能性も高まります。
        </p>
      </div>
    </div>
  );
};

export default StrategySettings;
