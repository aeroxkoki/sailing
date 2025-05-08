import React from 'react';
import { WindSettings as WindSettingsType } from '../../types';

interface WindSettingsProps {
  settings: WindSettingsType;
  onChange: <K extends keyof WindSettingsType>(key: K, value: WindSettingsType[K]) => void;
}

const WindSettings: React.FC<WindSettingsProps> = ({ settings, onChange }) => {
  return (
    <div className="space-y-4">
      <h3 className="text-base font-medium text-gray-300 mb-3">風向風速推定設定</h3>
      
      {/* アルゴリズム選択 */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-400">
          推定アルゴリズム
        </label>
        <select
          value={settings.algorithm}
          onChange={(e) => onChange('algorithm', e.target.value as WindSettingsType['algorithm'])}
          className="w-full px-3 py-2 bg-gray-800 text-white rounded-md border border-gray-700 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          <option value="simple">シンプル (高速・低精度)</option>
          <option value="bayesian">ベイジアン (中速・中精度)</option>
          <option value="combined">複合 (低速・高精度)</option>
        </select>
        <p className="text-xs text-gray-500">
          複合アルゴリズムは最も精度が高いですが、処理に時間がかかります。
        </p>
      </div>
      
      {/* 最小タック角度 */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-400">
          最小タック角度: {settings.minTackAngle}°
        </label>
        <input
          type="range"
          min="15"
          max="45"
          step="1"
          value={settings.minTackAngle}
          onChange={(e) => onChange('minTackAngle', parseInt(e.target.value))}
          className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
        />
        <div className="flex justify-between text-xs text-gray-500">
          <span>15°</span>
          <span>30°</span>
          <span>45°</span>
        </div>
      </div>
      
      {/* シフト検出 */}
      <div className="flex items-center space-x-3">
        <input
          type="checkbox"
          id="useShiftDetection"
          checked={settings.useShiftDetection}
          onChange={(e) => onChange('useShiftDetection', e.target.checked)}
          className="w-4 h-4 bg-gray-800 border-gray-700 rounded text-blue-500 focus:ring-0"
        />
        <label htmlFor="useShiftDetection" className="text-sm font-medium text-gray-400">
          風向シフト検出を有効にする
        </label>
      </div>
      <p className="text-xs text-gray-500 -mt-2">
        風向変化を自動検出し、シフトポイントを戦略分析に含めます。
      </p>
      
      {/* スムージング係数 */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-400">
          スムージング係数: {settings.smoothingFactor}%
        </label>
        <input
          type="range"
          min="0"
          max="100"
          step="5"
          value={settings.smoothingFactor}
          onChange={(e) => onChange('smoothingFactor', parseInt(e.target.value))}
          className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
        />
        <div className="flex justify-between text-xs text-gray-500">
          <span>0% (生データ)</span>
          <span>100% (最大)</span>
        </div>
      </div>
      
      <div className="border-t border-gray-700 pt-4 mt-6">
        <p className="text-xs text-gray-500">
          風向風速推定設定は、GPSデータからの風の状態推定アルゴリズムの挙動を調整します。高精度の推定が必要な場合は複合アルゴリズムを、処理速度が重要な場合はシンプルアルゴリズムを選択してください。
        </p>
      </div>
    </div>
  );
};

export default WindSettings;
