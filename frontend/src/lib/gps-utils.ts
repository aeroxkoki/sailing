// GPS座標のインターフェース
export interface GPSPoint {
  latitude: number;
  longitude: number;
  timestamp?: string | Date;
  speed?: number;
  course?: number;
  [key: string]: any;
}

/**
 * ファイルからGPSデータを解析する
 * 
 * @param file アップロードされたGPSデータファイル
 * @returns Promise<GPSPoint[]> GPS座標の配列
 */
export const parseGPSFile = async (file: File): Promise<GPSPoint[]> => {
  try {
    const text = await readFileAsText(file);
    const extension = file.name.split('.').pop()?.toLowerCase();
    
    if (extension === 'csv') {
      return parseCSV(text);
    } else if (extension === 'gpx') {
      return parseGPX(text);
    } else {
      throw new Error('未対応のファイル形式です');
    }
  } catch (error) {
    console.error('GPSファイル解析エラー:', error);
    return [];
  }
};

/**
 * ファイルをテキストとして読み込む
 * 
 * @param file 読み込むファイル
 * @returns Promise<string> ファイルの内容
 */
const readFileAsText = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => resolve(e.target?.result as string);
    reader.onerror = (e) => reject(e);
    reader.readAsText(file);
  });
};

/**
 * CSVテキストを解析してGPS座標の配列に変換
 * 
 * @param csvText CSVテキスト
 * @returns GPSPoint[] GPS座標の配列
 */
const parseCSV = (csvText: string): GPSPoint[] => {
  // 簡易的なCSV解析（実際の実装ではより堅牢なライブラリを使用することを推奨）
  const lines = csvText.trim().split('\n');
  const headers = lines[0].split(',').map(h => h.trim());
  
  // 必要なカラムのインデックスを特定
  const latIndex = headers.findIndex(h => 
    /^lat(itude)?$/i.test(h) || h === 'lat' || h === 'latitude'
  );
  const lonIndex = headers.findIndex(h => 
    /^lon(gitude)?$/i.test(h) || h === 'lon' || h === 'longitude'
  );
  const timeIndex = headers.findIndex(h => 
    /^time(stamp)?$/i.test(h) || h === 'time' || h === 'timestamp'
  );
  const speedIndex = headers.findIndex(h => 
    /^speed$/i.test(h) || h === 'speed'
  );
  const courseIndex = headers.findIndex(h => 
    /^course|bearing|heading$/i.test(h) || h === 'course' || h === 'bearing' || h === 'heading'
  );
  
  // 緯度経度が特定できない場合はエラー
  if (latIndex === -1 || lonIndex === -1) {
    throw new Error('CSVファイルに緯度・経度データが見つかりません');
  }
  
  // データ行の解析
  const points: GPSPoint[] = [];
  for (let i = 1; i < lines.length; i++) {
    const values = lines[i].split(',').map(v => v.trim());
    
    // 必須データ（緯度経度）が存在するか確認
    if (values.length <= Math.max(latIndex, lonIndex) || !values[latIndex] || !values[lonIndex]) {
      continue;
    }
    
    const point: GPSPoint = {
      latitude: parseFloat(values[latIndex]),
      longitude: parseFloat(values[lonIndex]),
    };
    
    // オプションデータの追加
    if (timeIndex !== -1 && values[timeIndex]) {
      point.timestamp = values[timeIndex];
    }
    
    if (speedIndex !== -1 && values[speedIndex]) {
      point.speed = parseFloat(values[speedIndex]);
    }
    
    if (courseIndex !== -1 && values[courseIndex]) {
      point.course = parseFloat(values[courseIndex]);
    }
    
    points.push(point);
  }
  
  return points;
};

/**
 * GPXテキストを解析してGPS座標の配列に変換
 * 
 * @param gpxText GPXテキスト
 * @returns GPSPoint[] GPS座標の配列
 */
const parseGPX = (gpxText: string): GPSPoint[] => {
  const parser = new DOMParser();
  const gpx = parser.parseFromString(gpxText, 'text/xml');
  
  // トラックポイントを取得
  const trackPoints = gpx.querySelectorAll('trkpt');
  if (trackPoints.length === 0) {
    throw new Error('GPXファイルにトラックポイントが見つかりません');
  }
  
  const points: GPSPoint[] = [];
  trackPoints.forEach(trackPoint => {
    const lat = trackPoint.getAttribute('lat');
    const lon = trackPoint.getAttribute('lon');
    
    if (!lat || !lon) return;
    
    const point: GPSPoint = {
      latitude: parseFloat(lat),
      longitude: parseFloat(lon),
    };
    
    // 時刻
    const timeElement = trackPoint.querySelector('time');
    if (timeElement && timeElement.textContent) {
      point.timestamp = timeElement.textContent;
    }
    
    // 速度
    const speedElement = trackPoint.querySelector('speed');
    if (speedElement && speedElement.textContent) {
      point.speed = parseFloat(speedElement.textContent);
    }
    
    // 方位
    const courseElement = trackPoint.querySelector('course');
    if (courseElement && courseElement.textContent) {
      point.course = parseFloat(courseElement.textContent);
    }
    
    points.push(point);
  });
  
  return points;
};

/**
 * 航跡の距離を計算（メートル単位）
 * 
 * @param points GPS座標の配列
 * @returns number 総距離（メートル）
 */
export const calculateTrackDistance = (points: GPSPoint[]): number => {
  if (points.length < 2) return 0;
  
  let totalDistance = 0;
  for (let i = 1; i < points.length; i++) {
    totalDistance += calculateDistance(
      points[i-1].latitude, points[i-1].longitude,
      points[i].latitude, points[i].longitude
    );
  }
  
  return totalDistance;
};

/**
 * 2点間の距離をハバーシン公式で計算（メートル単位）
 * 
 * @param lat1 緯度1
 * @param lon1 経度1
 * @param lat2 緯度2
 * @param lon2 経度2
 * @returns number 距離（メートル）
 */
export const calculateDistance = (
  lat1: number, lon1: number,
  lat2: number, lon2: number
): number => {
  const R = 6371000; // 地球の半径（メートル）
  const dLat = toRadians(lat2 - lat1);
  const dLon = toRadians(lon2 - lon1);
  
  const a = 
    Math.sin(dLat/2) * Math.sin(dLat/2) +
    Math.cos(toRadians(lat1)) * Math.cos(toRadians(lat2)) * 
    Math.sin(dLon/2) * Math.sin(dLon/2);
  
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  const distance = R * c;
  
  return distance;
};

/**
 * デフォルトのGPSデータを取得（デモ用）
 * 
 * @returns GPSPoint[] デフォルトのGPS座標の配列
 */
export const getDefaultGPSData = (): GPSPoint[] => {
  return [
    { latitude: 35.1, longitude: 139.8, timestamp: '2025-04-01T10:00:00Z', speed: 5.2 },
    { latitude: 35.102, longitude: 139.805, timestamp: '2025-04-01T10:01:00Z', speed: 5.5 },
    { latitude: 35.105, longitude: 139.81, timestamp: '2025-04-01T10:02:00Z', speed: 5.3 },
    { latitude: 35.108, longitude: 139.815, timestamp: '2025-04-01T10:03:00Z', speed: 5.1 },
    { latitude: 35.11, longitude: 139.82, timestamp: '2025-04-01T10:04:00Z', speed: 4.9 },
    { latitude: 35.108, longitude: 139.825, timestamp: '2025-04-01T10:05:00Z', speed: 5.0 },
    { latitude: 35.105, longitude: 139.83, timestamp: '2025-04-01T10:06:00Z', speed: 5.2 },
    { latitude: 35.102, longitude: 139.835, timestamp: '2025-04-01T10:07:00Z', speed: 5.4 },
    { latitude: 35.1, longitude: 139.84, timestamp: '2025-04-01T10:08:00Z', speed: 5.3 },
  ];
};

/**
 * 度からラジアンに変換
 * 
 * @param degrees 度
 * @returns number ラジアン
 */
const toRadians = (degrees: number): number => {
  return degrees * Math.PI / 180;
};

/**
 * GPSデータの処理と変換に関する追加ユーティリティ
 */

/**
 * GPSデータをGeoJSON形式に変換
 * 
 * @param points GPS座標の配列
 * @returns GeoJSON LineString形式のオブジェクト
 */
export const convertToGeoJSON = (points: GPSPoint[]): any => {
  return {
    type: 'Feature',
    properties: {},
    geometry: {
      type: 'LineString',
      coordinates: points.map(point => [point.longitude, point.latitude]),
    },
  };
};

/**
 * GPSデータの時間範囲を取得
 * 
 * @param points GPS座標の配列
 * @returns [開始時間, 終了時間] または null（時間情報がない場合）
 */
export const getTimeRange = (points: GPSPoint[]): [Date, Date] | null => {
  const timestamps = points
    .filter(point => point.timestamp)
    .map(point => new Date(point.timestamp as string));
  
  if (timestamps.length === 0) return null;
  
  return [
    new Date(Math.min(...timestamps.map(d => d.getTime()))),
    new Date(Math.max(...timestamps.map(d => d.getTime()))),
  ];
};

/**
 * GPSデータから速度統計を計算
 * 
 * @param points GPS座標の配列
 * @returns {min, max, avg} 速度の統計情報（ノット単位）
 */
export const calculateSpeedStats = (points: GPSPoint[]): { min: number, max: number, avg: number } => {
  const speedPoints = points.filter(point => typeof point.speed === 'number');
  
  if (speedPoints.length === 0) {
    return { min: 0, max: 0, avg: 0 };
  }
  
  const speeds = speedPoints.map(point => point.speed as number);
  const sum = speeds.reduce((a, b) => a + b, 0);
  
  return {
    min: Math.min(...speeds),
    max: Math.max(...speeds),
    avg: sum / speeds.length,
  };
};
