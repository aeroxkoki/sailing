import { GpsPoint, WindDataPoint, StrategyPoint } from './gps';

/**
 * 分析データの型定義
 */
export interface AnalysisData {
  sessionId: string | null;         // セッションID
  fileName: string | null;          // ファイル名
  startTime: number;                // 開始時間（UNIXタイムスタンプ・ミリ秒）
  endTime: number;                  // 終了時間（UNIXタイムスタンプ・ミリ秒）
  currentTime: number;              // 現在の時間（UNIXタイムスタンプ・ミリ秒）
  gpsData: GpsPoint[];              // GPSデータポイント
  windData: WindDataPoint[];        // 風向風速データポイント
  strategyPoints: StrategyPoint[];  // 戦略ポイント
  averageWindDirection: number;     // 平均風向（度数）
  averageWindSpeed: number;         // 平均風速（ノット）
  maxWindSpeed: number;             // 最大風速（ノット）
  windStability: number;            // 風の安定度（0-1）
  averageSpeed: number;             // 平均速度（ノット）
  maxSpeed: number;                 // 最高速度（ノット）
  upwindVMG: number;                // 風上VMG（ノット）
  downwindVMG: number;              // 風下VMG（ノット）
  trackLength: number;              // 航跡の長さ（海里）
  totalTacks: number;               // タックの総数
  totalJibes: number;               // ジャイブの総数
  tackEfficiency: number;           // タック効率（0-1）
  jibeEfficiency: number;           // ジャイブ効率（0-1）
  performanceScore: number;         // パフォーマンススコア（0-1）
}

/**
 * エクスポート形式の型定義
 */
export type ExportFormat = 'pdf' | 'csv' | 'gpx' | 'json';

/**
 * APIのエラーレスポンスの型定義
 */
export interface ApiError {
  status: number;
  message: string;
  data?: any;
}
