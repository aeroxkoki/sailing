// モックデータファイル（APIが利用できない場合のデモ用）
import { GpsPoint, WindDataPoint, StrategyPoint, StrategyPointType } from '../types';

// GPSトラックのモックデータ
export const mockGpsData: GpsPoint[] = [
  // サンプルGPSポイント（実際には200-300ポイントほど必要）
  { timestamp: 1621500000000, latitude: 35.65, longitude: 139.76, speed: 5.2, heading: 120 },
  { timestamp: 1621500010000, latitude: 35.651, longitude: 139.762, speed: 5.5, heading: 122 },
  { timestamp: 1621500020000, latitude: 35.652, longitude: 139.764, speed: 5.3, heading: 125 },
  // ... 他のポイント
];

// 風向風速のモックデータ
export const mockWindData: WindDataPoint[] = [
  // サンプル風データポイント
  { timestamp: 1621500000000, latitude: 35.65, longitude: 139.76, direction: 180, speed: 12, confidence: 0.8 },
  { timestamp: 1621500010000, latitude: 35.651, longitude: 139.762, direction: 182, speed: 11.5, confidence: 0.85 },
  { timestamp: 1621500020000, latitude: 35.652, longitude: 139.764, direction: 185, speed: 12.2, confidence: 0.9 },
  // ... 他のポイント
];

// 戦略ポイントのモックデータ
export const mockStrategyPoints: StrategyPoint[] = [
  // サンプル戦略ポイント
  { 
    id: '1', 
    timestamp: 1621500050000, 
    latitude: 35.653, 
    longitude: 139.766, 
    type: StrategyPointType.TACK, 
    details: { efficiency: 0.85, timeLoss: 4.5 }, 
    evaluation: { score: 0.8, comments: '良好なタックパフォーマンス' } 
  },
  { 
    id: '2', 
    timestamp: 1621500150000, 
    latitude: 35.655, 
    longitude: 139.77, 
    type: StrategyPointType.JIBE, 
    details: { efficiency: 0.75, timeLoss: 6.2 }, 
    evaluation: { score: 0.7, comments: '平均的なジャイブパフォーマンス' } 
  },
  // ... 他の戦略ポイント
];

// モックセッションデータ
export const mockSession = {
  id: 'mock-session-001',
  name: 'デモセッション',
  location: '東京湾',
  startTime: 1621500000000,
  endTime: 1621505000000,
  weather: {
    windDirection: 180,
    windSpeed: 12,
    temperature: 22,
    conditions: '晴れ'
  },
  boat: {
    name: 'デモボート',
    type: 'レーザー',
    length: 4.23
  }
};

// モック分析結果
export const mockAnalysisResult = {
  sessionId: mockSession.id,
  fileName: 'demo_data.gpx',
  startTime: mockSession.startTime,
  endTime: mockSession.endTime,
  currentTime: mockSession.startTime,
  gpsData: mockGpsData,
  windData: mockWindData,
  strategyPoints: mockStrategyPoints,
  averageWindDirection: 182.5,
  averageWindSpeed: 12.1,
  upwindVMG: 3.2,
  downwindVMG: 4.5,
  trackLength: 8.5,
  totalTacks: 5,
  totalJibes: 3,
  performanceScore: 0.78
};

// データのまとめ
const mockData = {
  gpsData: mockGpsData,
  windData: mockWindData,
  strategyPoints: mockStrategyPoints,
  session: mockSession,
  analysisResult: mockAnalysisResult
};

export default mockData;
