/**
 * 風向風速推定の設定の型定義
 */
export interface WindSettings {
  algorithm: 'simple' | 'bayesian' | 'combined'; // 推定アルゴリズム
  minTackAngle: number;                         // 最小タック角度（度数）
  useShiftDetection: boolean;                    // シフト検出を使用するか
  smoothingFactor: number;                      // スムージング係数（0-100）
}

/**
 * 戦略検出の設定の型定義
 */
export interface StrategySettings {
  sensitivity: number;                          // 感度（0-100）
  detectTypes: string[];                        // 検出するポイントのタイプ
  minConfidence: number;                        // 最小信頼度（0-100）
}

/**
 * 表示設定の型定義
 */
export interface DisplaySettings {
  colorScheme: 'speed' | 'vmg' | 'heading';     // 色分けスキーム
  showLabels: boolean;                          // ラベルを表示するか
  mapStyle: 'dark' | 'satellite' | 'nautical';  // マップスタイル
}

/**
 * 詳細設定の型定義
 */
export interface AdvancedSettings {
  boatType: string;                              // ボートタイプ
  polarFile: File | null;                        // ポーラーファイル
  timeFormat: '12h' | '24h';                     // 時間フォーマット
  useGPSAltitude: boolean;                       // GPS高度を使用するか
}

/**
 * 全設定の型定義
 */
export interface AppSettings {
  wind: WindSettings;
  strategy: StrategySettings;
  display: DisplaySettings;
  advanced: AdvancedSettings;
}
