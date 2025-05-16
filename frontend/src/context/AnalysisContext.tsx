import React, { createContext, useState, useContext, ReactNode, useEffect } from 'react';
import { AnalysisData, ExportFormat, AppSettings, ApiError } from '../types';
import api from '../lib/api';
import mockData from '../lib/mock-data';

// 初期データ
const initialAnalysisData: AnalysisData = {
  sessionId: null,
  fileName: null,
  startTime: 0,
  endTime: 0,
  currentTime: 0,
  gpsData: [],
  windData: [],
  strategyPoints: [],
  averageWindDirection: 0,
  averageWindSpeed: 0,
  maxWindSpeed: 0,
  windStability: 0,
  averageSpeed: 0,
  maxSpeed: 0,
  upwindVMG: 0,
  downwindVMG: 0,
  trackLength: 0,
  totalTacks: 0,
  totalJibes: 0,
  tackEfficiency: 0,
  jibeEfficiency: 0,
  performanceScore: 0,
};

// コンテキスト型定義
interface AnalysisContextType {
  data: AnalysisData;
  isAnalyzing: boolean;
  error: string | null;
  isOfflineMode: boolean;
  apiStatus: string;
  uploadFile: (file: File, settings?: Partial<AppSettings>) => Promise<void>;
  loadDemoData: () => void;
  applySettings: (settings: Partial<AppSettings>) => Promise<void>;
  setCurrentTime: (time: number) => void;
  exportResults: (format: ExportFormat, includeSettings?: boolean) => Promise<Blob>;
  toggleOfflineMode: (enabled: boolean) => void;
}

// コンテキスト作成
export const AnalysisContext = createContext<AnalysisContextType>({
  data: initialAnalysisData,
  isAnalyzing: false,
  error: null,
  isOfflineMode: false,
  apiStatus: 'unknown',
  uploadFile: async () => {},
  loadDemoData: () => {},
  applySettings: async () => {},
  setCurrentTime: () => {},
  exportResults: async () => new Blob(),
  toggleOfflineMode: () => {},
});

// コンテキストプロバイダーコンポーネント
interface AnalysisProviderProps {
  children: ReactNode;
}

export const AnalysisProvider: React.FC<AnalysisProviderProps> = ({ children }) => {
  const [data, setData] = useState<AnalysisData>(initialAnalysisData);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [isOfflineMode, setIsOfflineMode] = useState<boolean>(api.isOfflineMode());
  const [apiStatus, setApiStatus] = useState<string>('unknown');
  
  // 初期化時にAPIの状態をチェック
  useEffect(() => {
    const checkApiStatus = async () => {
      try {
        const health = await api.checkHealth();
        setApiStatus(health.status);
        if (health.offlineMode) {
          setIsOfflineMode(true);
        }
      } catch (err) {
        console.error('API status check failed:', err);
        setApiStatus('error');
      }
    };
    
    checkApiStatus();
  }, []);
  
  // オフラインモードの切り替え
  const toggleOfflineMode = (enabled: boolean): void => {
    api.toggleOfflineMode(enabled);
    setIsOfflineMode(enabled);
    setApiStatus(enabled ? 'offline' : 'unknown');
    
    // オフラインモードに切り替える場合はエラーをクリア
    if (enabled) {
      setError(null);
    }
  };
  
  // デモデータの読み込み
  const loadDemoData = (): void => {
    setIsAnalyzing(true);
    
    setTimeout(() => {
      setData(mockData.analysisResult as AnalysisData);
      setIsAnalyzing(false);
    }, 1000); // 1秒後に読み込み完了（ローディング表示のため）
  };
  
  // ファイルアップロードと分析
  const uploadFile = async (file: File, settings?: Partial<AppSettings>): Promise<void> => {
    setIsAnalyzing(true);
    setError(null);
    
    // オフラインモードの場合は、モックデータを使用
    if (isOfflineMode) {
      setTimeout(() => {
        setData({
          ...mockData.analysisResult as AnalysisData,
          fileName: file.name
        });
        setIsAnalyzing(false);
      }, 1500);
      return;
    }
    
    try {
      const response = await api.analyzeGpsData(file, settings);
      
      // レスポンスを分析データに変換
      setData({
        ...response.data,
        fileName: file.name,
        currentTime: response.data.startTime
      });
    } catch (err: any) {
      const apiError = err as ApiError;
      setError(apiError.message || '分析中にエラーが発生しました');
      console.error('Analysis error:', apiError);
    } finally {
      setIsAnalyzing(false);
    }
  };
  
  // 設定適用と再分析
  const applySettings = async (settings: Partial<AppSettings>): Promise<void> => {
    if (!data.sessionId) return;
    
    setIsAnalyzing(true);
    setError(null);
    
    try {
      // 風向風速推定
      const windResponse = await api.estimateWind(data.sessionId, settings.wind);
      
      // 戦略ポイント検出
      const strategyResponse = await api.detectStrategyPoints(
        data.sessionId, 
        settings.strategy
      );
      
      // データ更新
      setData(prevData => ({
        ...prevData,
        windData: windResponse.data.windData,
        averageWindDirection: windResponse.data.averageWindDirection,
        averageWindSpeed: windResponse.data.averageWindSpeed,
        maxWindSpeed: windResponse.data.maxWindSpeed,
        windStability: windResponse.data.windStability,
        strategyPoints: strategyResponse.data.strategyPoints,
        totalTacks: strategyResponse.data.totalTacks,
        totalJibes: strategyResponse.data.totalJibes,
        tackEfficiency: strategyResponse.data.tackEfficiency,
        jibeEfficiency: strategyResponse.data.jibeEfficiency,
        performanceScore: strategyResponse.data.performanceScore
      }));
    } catch (err: any) {
      const apiError = err as ApiError;
      setError(apiError.message || '再分析中にエラーが発生しました');
      console.error('Reanalysis error:', apiError);
    } finally {
      setIsAnalyzing(false);
    }
  };
  
  // 現在時間の設定
  const setCurrentTime = (time: number): void => {
    setData(prevData => ({
      ...prevData,
      currentTime: time
    }));
  };
  
  // 結果のエクスポート
  const exportResults = async (format: ExportFormat, includeSettings: boolean = true): Promise<Blob> => {
    if (!data.sessionId) {
      throw new Error('エクスポートするセッションがありません');
    }
    
    try {
      const response = await api.exportAnalysis(data.sessionId, format, includeSettings);
      return response.data as Blob;
    } catch (err: any) {
      const apiError = err as ApiError;
      throw new Error(apiError.message || 'エクスポート中にエラーが発生しました');
    }
  };
  
  // 提供する値
  const contextValue: AnalysisContextType = {
    data,
    isAnalyzing,
    error,
    isOfflineMode,
    apiStatus,
    uploadFile,
    loadDemoData,
    applySettings,
    setCurrentTime,
    exportResults,
    toggleOfflineMode
  };
  
  return (
    <AnalysisContext.Provider value={contextValue}>
      {children}
    </AnalysisContext.Provider>
  );
};

// カスタムフック
export const useAnalysis = (): AnalysisContextType => useContext(AnalysisContext);
