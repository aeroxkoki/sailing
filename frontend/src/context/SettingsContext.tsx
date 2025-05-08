import React, { createContext, useState, useContext, ReactNode } from 'react';
import { AppSettings, WindSettings, StrategySettings, DisplaySettings, AdvancedSettings } from '../types';

// デフォルト設定
const defaultSettings: AppSettings = {
  wind: {
    algorithm: 'combined', // 'simple', 'bayesian', 'combined'
    minTackAngle: 30,
    useShiftDetection: true,
    smoothingFactor: 50,
  },
  strategy: {
    sensitivity: 70, // 0-100
    detectTypes: ['tack', 'jibe', 'mark', 'shift'],
    minConfidence: 50, // 0-100
  },
  display: {
    colorScheme: 'speed', // 'speed', 'vmg', 'heading'
    showLabels: true,
    mapStyle: 'dark', // 'dark', 'satellite', 'nautical'
  },
  advanced: {
    boatType: 'default', // 'default', 'laser', 'optimist', '470', '49er'
    polarFile: null, // カスタムポーラーファイル
    timeFormat: '24h', // '12h', '24h'
    useGPSAltitude: false,
  }
};

// コンテキストの型定義
interface SettingsContextType {
  settings: AppSettings;
  updateSettings: <K extends keyof AppSettings, T extends keyof AppSettings[K]>(
    category: K, 
    key: T, 
    value: AppSettings[K][T]
  ) => void;
  resetSettings: () => void;
}

// コンテキスト作成
export const SettingsContext = createContext<SettingsContextType>({
  settings: defaultSettings,
  updateSettings: () => {},
  resetSettings: () => {},
});

// コンテキストプロバイダーコンポーネント
interface SettingsProviderProps {
  children: ReactNode;
}

export const SettingsProvider: React.FC<SettingsProviderProps> = ({ children }) => {
  const [settings, setSettings] = useState<AppSettings>(defaultSettings);
  
  // 設定更新関数
  const updateSettings = <K extends keyof AppSettings, T extends keyof AppSettings[K]>(
    category: K, 
    key: T, 
    value: AppSettings[K][T]
  ): void => {
    setSettings(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [key]: value
      }
    }));
  };
  
  // 設定リセット関数
  const resetSettings = (): void => {
    setSettings(defaultSettings);
  };
  
  // 提供する値
  const contextValue: SettingsContextType = {
    settings,
    updateSettings,
    resetSettings,
  };
  
  return (
    <SettingsContext.Provider value={contextValue}>
      {children}
    </SettingsContext.Provider>
  );
};

// カスタムフック
export const useSettings = (): SettingsContextType => useContext(SettingsContext);
