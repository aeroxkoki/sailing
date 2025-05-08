/**
 * 日時のフォーマット関数
 * @param date 日時オブジェクト
 * @param options フォーマットオプション
 * @returns フォーマットされた文字列
 */
export const formatTime = (date: Date, options?: Intl.DateTimeFormatOptions): string => {
  const defaultOptions: Intl.DateTimeFormatOptions = {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  };

  const mergedOptions = { ...defaultOptions, ...options };
  return date.toLocaleTimeString(undefined, mergedOptions);
};

/**
 * 風向を人間が読みやすい方位に変換
 * @param degrees 風向の角度 (0-360)
 * @returns 風向の表記 (N, NE, E, など)
 */
export const formatWindDirection = (degrees: number): string => {
  const directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW', 'N'];
  const index = Math.round(degrees / 22.5);
  return directions[index];
};

/**
 * 風速を指定された単位でフォーマット
 * @param speed 風速 (ノット)
 * @param unit 単位 ('knots', 'm/s', 'km/h')
 * @param precision 小数点以下の桁数
 * @returns フォーマットされた風速
 */
export const formatWindSpeed = (speed: number, unit: 'knots' | 'm/s' | 'km/h' = 'knots', precision: number = 1): string => {
  let converted = speed;
  let unitSymbol = 'kts';
  
  switch (unit) {
    case 'm/s':
      converted = speed * 0.514444;
      unitSymbol = 'm/s';
      break;
    case 'km/h':
      converted = speed * 1.852;
      unitSymbol = 'km/h';
      break;
  }
  
  return `${converted.toFixed(precision)} ${unitSymbol}`;
};

/**
 * 距離をフォーマット
 * @param meters 距離 (メートル)
 * @param precision 小数点以下の桁数
 * @returns フォーマットされた距離
 */
export const formatDistance = (meters: number, precision: number = 1): string => {
  if (meters < 1000) {
    return `${meters.toFixed(precision)} m`;
  } else {
    return `${(meters / 1000).toFixed(precision)} km`;
  }
};

/**
 * 期間を HH:MM:SS 形式でフォーマット
 * @param milliseconds ミリ秒
 * @returns フォーマットされた期間
 */
export const formatDuration = (milliseconds: number): string => {
  const seconds = Math.floor(milliseconds / 1000);
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainingSeconds = seconds % 60;
  
  return [
    hours.toString().padStart(2, '0'),
    minutes.toString().padStart(2, '0'),
    remainingSeconds.toString().padStart(2, '0')
  ].join(':');
};

/**
 * JSONデータを整形された文字列に変換
 * @param data JSONデータ
 * @returns 整形された文字列
 */
export const formatJson = (data: any): string => {
  try {
    return JSON.stringify(data, null, 2);
  } catch (error) {
    return `Error formatting JSON: ${error}`;
  }
};
