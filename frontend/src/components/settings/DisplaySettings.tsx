import React from 'react';
import { DisplaySettings as DisplaySettingsType } from '../../types';

interface DisplaySettingsProps {
  settings: DisplaySettingsType;
  onChange: <K extends keyof DisplaySettingsType>(key: K, value: DisplaySettingsType[K]) => void;
}

const DisplaySettings: React.FC<DisplaySettingsProps> = ({ settings, onChange }) => {
  // カラースキームのオプション
  const colorSchemes = [
    { value: 'speed', label: '速度', description: '速度によって色分けされます（青：低速 → 赤：高速）' },
    { value: 'vmg', label: 'VMG', description: '風上/風下方向への有効速度で色分けされます' },
    { value: 'heading', label: '方位', description: '進行方向によって色分けされます（0°～360°）' },
  ];
  
  // マップスタイルのオプション
  const mapStyles = [
    { value: 'dark', label: 'ダーク', description: '暗い背景（夜間に最適）' },
    { value: 'satellite', label: '衛星写真', description: '実際の地形・地物が表示されます' },
    { value: 'nautical', label: '海図', description: '航海用の地図スタイル' },
  ];
  
  return (
    <div className="space-y-4">
      <h3 className="text-base font-medium text-gray-300 mb-3">表示設定</h3>
      
      {/* カラースキーム */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-400">
          カラースキーム
        </label>
        <div className="space-y-2">
          {colorSchemes.map(scheme => (
            <div key={scheme.value} className="flex items-start space-x-2">
              <input
                type="radio"
                id={`color-${scheme.value}`}
                value={scheme.value}
                checked={settings.colorScheme === scheme.value}
                onChange={() => onChange('colorScheme', scheme.value as DisplaySettingsType['colorScheme'])}
                className="mt-1 w-4 h-4 bg-gray-800 border-gray-700 text-blue-500 focus:ring-0"
              />
              <div>
                <label htmlFor={`color-${scheme.value}`} className="block text-sm text-gray-300">
                  {scheme.label}
                </label>
                <p className="text-xs text-gray-500">{scheme.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {/* マップスタイル */}
      <div className="space-y-2 mt-4">
        <label className="block text-sm font-medium text-gray-400">
          マップスタイル
        </label>
        <div className="grid grid-cols-3 gap-2">
          {mapStyles.map(style => (
            <button
              key={style.value}
              type="button"
              onClick={() => onChange('mapStyle', style.value as DisplaySettingsType['mapStyle'])}
              className={`p-2 rounded border ${
                settings.mapStyle === style.value
                  ? 'border-blue-500 bg-blue-900 bg-opacity-20'
                  : 'border-gray-700 hover:border-gray-600'
              }`}
            >
              <span className="block text-xs font-medium text-center text-gray-300">
                {style.label}
              </span>
            </button>
          ))}
        </div>
        <p className="text-xs text-gray-500">
          選択したマップスタイルによってデータの視認性が変わることがあります。
        </p>
      </div>
      
      {/* ラベル表示 */}
      <div className="flex items-center space-x-3 mt-4">
        <input
          type="checkbox"
          id="showLabels"
          checked={settings.showLabels}
          onChange={(e) => onChange('showLabels', e.target.checked)}
          className="w-4 h-4 bg-gray-800 border-gray-700 rounded text-blue-500 focus:ring-0"
        />
        <label htmlFor="showLabels" className="text-sm font-medium text-gray-400">
          ポイントラベルを表示
        </label>
      </div>
      <p className="text-xs text-gray-500 ml-7">
        戦略ポイントの詳細情報をマップ上に表示します。
      </p>
      
      <div className="border-t border-gray-700 pt-4 mt-6">
        <p className="text-xs text-gray-500">
          表示設定では、データの視覚化方法をカスタマイズできます。ご自身の好みや用途に合わせて設定を調整してください。
        </p>
      </div>
    </div>
  );
};

export default DisplaySettings;
