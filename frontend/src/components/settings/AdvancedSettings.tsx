import React, { useRef } from 'react';
import { AdvancedSettings as AdvancedSettingsType } from '../../types';

interface AdvancedSettingsProps {
  settings: AdvancedSettingsType;
  onChange: <K extends keyof AdvancedSettingsType>(key: K, value: AdvancedSettingsType[K]) => void;
}

const AdvancedSettings: React.FC<AdvancedSettingsProps> = ({ settings, onChange }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // ボートタイプのオプション
  const boatTypes = [
    { value: 'default', label: 'デフォルト' },
    { value: 'laser', label: 'レーザー' },
    { value: 'optimist', label: 'オプティミスト' },
    { value: '470', label: '470' },
    { value: '49er', label: '49er' },
    { value: 'custom', label: 'カスタム' },
  ];
  
  // ファイル選択ハンドラ
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onChange('polarFile', file);
    }
  };
  
  // ファイル選択ダイアログを開く
  const openFileDialog = () => {
    fileInputRef.current?.click();
  };
  
  return (
    <div className="space-y-4">
      <h3 className="text-base font-medium text-gray-300 mb-3">詳細設定</h3>
      
      {/* ボートタイプ */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-400">
          ボートタイプ
        </label>
        <select
          value={settings.boatType}
          onChange={(e) => onChange('boatType', e.target.value)}
          className="w-full px-3 py-2 bg-gray-800 text-white rounded-md border border-gray-700 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          {boatTypes.map(type => (
            <option key={type.value} value={type.value}>
              {type.label}
            </option>
          ))}
        </select>
        <p className="text-xs text-gray-500">
          ボートのパフォーマンス特性（ポーラー）を決定します。
        </p>
      </div>
      
      {/* カスタムポーラーファイル */}
      {settings.boatType === 'custom' && (
        <div className="space-y-2 mt-4">
          <label className="block text-sm font-medium text-gray-400">
            カスタムポーラーファイル
          </label>
          <div 
            onClick={openFileDialog}
            className="flex items-center justify-between px-3 py-2 bg-gray-800 border border-gray-700 rounded-md cursor-pointer hover:bg-gray-750"
          >
            <span className="text-sm text-gray-400 truncate">
              {settings.polarFile ? settings.polarFile.name : 'CSVファイルを選択...'}
            </span>
            <button
              type="button"
              className="ml-2 p-1 rounded hover:bg-gray-700 text-blue-400"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
            </button>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            className="hidden"
            onChange={handleFileSelect}
          />
          <p className="text-xs text-gray-500">
            ポーラーファイル（CSV形式）は風速・風向に対する艇速を定義します。
          </p>
        </div>
      )}
      
      {/* 時間フォーマット */}
      <div className="space-y-2 mt-4">
        <label className="block text-sm font-medium text-gray-400">
          時間表示形式
        </label>
        <div className="flex space-x-4">
          <div className="flex items-center space-x-2">
            <input
              type="radio"
              id="time-24h"
              checked={settings.timeFormat === '24h'}
              onChange={() => onChange('timeFormat', '24h')}
              className="w-4 h-4 bg-gray-800 border-gray-700 text-blue-500 focus:ring-0"
            />
            <label htmlFor="time-24h" className="text-sm text-gray-400">
              24時間形式
            </label>
          </div>
          <div className="flex items-center space-x-2">
            <input
              type="radio"
              id="time-12h"
              checked={settings.timeFormat === '12h'}
              onChange={() => onChange('timeFormat', '12h')}
              className="w-4 h-4 bg-gray-800 border-gray-700 text-blue-500 focus:ring-0"
            />
            <label htmlFor="time-12h" className="text-sm text-gray-400">
              12時間形式
            </label>
          </div>
        </div>
      </div>
      
      {/* GPS高度を使用 */}
      <div className="flex items-center space-x-3 mt-4">
        <input
          type="checkbox"
          id="useGPSAltitude"
          checked={settings.useGPSAltitude}
          onChange={(e) => onChange('useGPSAltitude', e.target.checked)}
          className="w-4 h-4 bg-gray-800 border-gray-700 rounded text-blue-500 focus:ring-0"
        />
        <label htmlFor="useGPSAltitude" className="text-sm font-medium text-gray-400">
          GPS高度情報を使用
        </label>
      </div>
      <p className="text-xs text-gray-500 ml-7">
        高度情報を分析に含めます（不正確な場合があります）。
      </p>
      
      <div className="border-t border-gray-700 pt-4 mt-6">
        <p className="text-xs text-gray-500">
          詳細設定は、分析アルゴリズムの高度なパラメータを調整します。特別な要件がない限り、デフォルト設定のままご利用ください。
        </p>
      </div>
    </div>
  );
};

export default AdvancedSettings;
