/**
 * GPSデータポイントの型定義
 */
export interface GpsPoint {
  id?: string;            // ポイントID
  timestamp: number;      // UNIXタイムスタンプ（ミリ秒）
  latitude: number;       // 緯度（度数）
  longitude: number;      // 経度（度数）
  speed?: number;         // 速度（ノット）
  heading?: number;       // 方位角（度数）
  altitude?: number;      // 高度（メートル）
  accuracy?: number;      // 位置精度（メートル）
  additional?: Record<string, any>; // その他のデータ
}

/**
 * 風向風速データポイントの型定義
 */
export interface WindDataPoint {
  id?: string;            // ポイントID
  timestamp: number;      // UNIXタイムスタンプ（ミリ秒）
  latitude: number;       // 緯度（度数）
  longitude: number;      // 経度（度数）
  direction: number;      // 風向（度数）
  speed: number;          // 風速（ノット）
  confidence?: number;    // 信頼度（0-1）
}

/**
 * 戦略ポイントの種類
 */
export enum StrategyPointType {
  TACK = 'tack',
  JIBE = 'jibe',
  MARK_ROUNDING = 'mark_rounding',
  WIND_SHIFT = 'wind_shift',
  LAYLINE = 'layline',
  START = 'start',
  FINISH = 'finish'
}

/**
 * 戦略ポイントの型定義
 */
export interface StrategyPoint {
  id: string;             // ポイントID
  timestamp: number;      // UNIXタイムスタンプ（ミリ秒）
  latitude: number;       // 緯度（度数）
  longitude: number;      // 経度（度数）
  type: StrategyPointType; // ポイントの種類
  details?: {             // 詳細情報
    duration?: number;    // 所要時間（秒）
    speedLoss?: number;   // 速度損失（ノット）
    angleChange?: number; // 角度変化（度数）
    [key: string]: any;
  };
  evaluation?: {          // 評価情報
    score?: number;       // 評価スコア（0-1）
    comments?: string;    // 評価コメント
    [key: string]: any;
  };
}

/**
 * ボートデータの型定義
 */
export interface BoatData {
  id: string;             // データID
  name: string;           // ボート名
  boatType?: string;      // ボートタイプ
  gpsPoints: GpsPoint[];  // GPSデータポイント
}
