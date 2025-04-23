import React, { useEffect, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

// コンポーネントのプロップスの型定義
interface MapViewProps {
  gpsData: any[];
  windData?: any[];
  strategyPoints?: any[];
  height?: string | number;
  width?: string | number;
  showWindLayer?: boolean;
  showStrategyPoints?: boolean;
}

// マップビューコンポーネント
const MapView: React.FC<MapViewProps> = ({
  gpsData,
  windData = [],
  strategyPoints = [],
  height = '500px',
  width = '100%',
  showWindLayer = true,
  showStrategyPoints = true,
}) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const [isMapLoaded, setIsMapLoaded] = useState(false);

  // マップの初期化
  useEffect(() => {
    if (!mapContainer.current) return;
    
    // マップが既に初期化されていれば何もしない
    if (map.current) return;
    
    // 初期表示位置の計算
    let initialCenter: [number, number] = [139.7, 35.7]; // デフォルト: 東京湾
    let initialZoom = 12;
    
    // GPSデータがある場合は、そのデータの中心を使用
    if (gpsData && gpsData.length > 0) {
      const lats = gpsData.map(point => point.latitude);
      const lons = gpsData.map(point => point.longitude);
      
      const minLat = Math.min(...lats);
      const maxLat = Math.max(...lats);
      const minLon = Math.min(...lons);
      const maxLon = Math.max(...lons);
      
      initialCenter = [(minLon + maxLon) / 2, (minLat + maxLat) / 2];
      
      // ズームレベルの計算（単純なヒューリスティック）
      const latDiff = maxLat - minLat;
      const lonDiff = maxLon - minLon;
      const maxDiff = Math.max(latDiff, lonDiff);
      
      if (maxDiff > 0.1) initialZoom = 10;
      else if (maxDiff > 0.05) initialZoom = 11;
      else if (maxDiff > 0.01) initialZoom = 13;
      else initialZoom = 14;
    }
    
    // MapLibre GLマップの初期化
    const mapInstance = new maplibregl.Map({
      container: mapContainer.current,
      style: 'https://demotiles.maplibre.org/style.json', // 無料の地図スタイル
      center: initialCenter,
      zoom: initialZoom,
    });
    
    // コントロールの追加
    mapInstance.addControl(new maplibregl.NavigationControl(), 'top-right');
    mapInstance.addControl(new maplibregl.ScaleControl(), 'bottom-left');
    
    // マップの参照を保存
    map.current = mapInstance;
    
    // マップ読み込み完了のハンドリング
    mapInstance.on('load', () => {
      setIsMapLoaded(true);
    });
    
    // クリーンアップ関数
    return () => {
      mapInstance.remove();
      map.current = null;
    };
  }, []);
  
  // GPSデータの表示
  useEffect(() => {
    if (!map.current || !isMapLoaded || !gpsData || gpsData.length === 0) return;
    
    const mapInstance = map.current;
    
    // 既存のGPSトラックレイヤーを削除
    if (mapInstance.getSource('gps-track')) {
      mapInstance.removeLayer('gps-track-line');
      mapInstance.removeSource('gps-track');
    }
    
    // GeoJSONデータの作成
    const geojson = {
      type: 'Feature',
      properties: {},
      geometry: {
        type: 'LineString',
        coordinates: gpsData.map(point => [point.longitude, point.latitude]),
      },
    };
    
    // ソースの追加
    mapInstance.addSource('gps-track', {
      type: 'geojson',
      data: geojson as any,
    });
    
    // レイヤーの追加
    mapInstance.addLayer({
      id: 'gps-track-line',
      type: 'line',
      source: 'gps-track',
      layout: {
        'line-join': 'round',
        'line-cap': 'round',
      },
      paint: {
        'line-color': '#0080ff',
        'line-width': 3,
      },
    });
    
    // ビューポートをGPSトラックに合わせる
    const coordinates = gpsData.map(point => [point.longitude, point.latitude]);
    const bounds = coordinates.reduce((bounds, coord) => {
      return bounds.extend(coord as [number, number]);
    }, new maplibregl.LngLatBounds(coordinates[0] as [number, number], coordinates[0] as [number, number]));
    
    mapInstance.fitBounds(bounds, {
      padding: 50,
      maxZoom: 15,
    });
  }, [gpsData, isMapLoaded]);
  
  // 風データレイヤーの表示
  useEffect(() => {
    if (!map.current || !isMapLoaded || !windData || windData.length === 0 || !showWindLayer) return;
    
    const mapInstance = map.current;
    
    // 既存の風レイヤーを削除
    if (mapInstance.getSource('wind-data')) {
      mapInstance.removeLayer('wind-direction');
      mapInstance.removeSource('wind-data');
    }
    
    // GeoJSONポイントデータの作成
    const points = windData.map(point => ({
      type: 'Feature',
      properties: {
        direction: point.direction,
        speed: point.speed,
        color: getWindSpeedColor(point.speed),
      },
      geometry: {
        type: 'Point',
        coordinates: [point.longitude, point.latitude],
      },
    }));
    
    // ソースの追加
    mapInstance.addSource('wind-data', {
      type: 'geojson',
      data: {
        type: 'FeatureCollection',
        features: points,
      },
    });
    
    // 風向を示す矢印のシンボルレイヤーを追加
    mapInstance.loadImage(
      'https://docs.mapbox.com/mapbox-gl-js/assets/custom_marker.png',
      (error, image) => {
        if (error) throw error;
        
        if (!mapInstance.hasImage('arrow')) {
          mapInstance.addImage('arrow', image!);
        }
        
        mapInstance.addLayer({
          id: 'wind-direction',
          type: 'symbol',
          source: 'wind-data',
          layout: {
            'icon-image': 'arrow',
            'icon-size': ['interpolate', ['linear'], ['get', 'speed'], 0, 0.5, 15, 1.5],
            'icon-rotate': ['get', 'direction'],
            'icon-allow-overlap': true,
            'icon-ignore-placement': true,
          },
          paint: {
            'icon-color': ['get', 'color'],
            'icon-opacity': 0.8,
          },
        });
      }
    );
  }, [windData, isMapLoaded, showWindLayer]);
  
  // 戦略ポイントの表示
  useEffect(() => {
    if (!map.current || !isMapLoaded || !strategyPoints || strategyPoints.length === 0 || !showStrategyPoints) return;
    
    const mapInstance = map.current;
    
    // 既存の戦略ポイントレイヤーを削除
    if (mapInstance.getSource('strategy-points')) {
      mapInstance.removeLayer('strategy-points-layer');
      mapInstance.removeSource('strategy-points');
    }
    
    // GeoJSONポイントデータの作成
    const points = strategyPoints.map(point => ({
      type: 'Feature',
      properties: {
        type: point.strategy_type,
        confidence: point.confidence,
        color: getStrategyPointColor(point.strategy_type),
        description: getStrategyPointDescription(point),
      },
      geometry: {
        type: 'Point',
        coordinates: [point.longitude, point.latitude],
      },
    }));
    
    // ソースの追加
    mapInstance.addSource('strategy-points', {
      type: 'geojson',
      data: {
        type: 'FeatureCollection',
        features: points,
      },
    });
    
    // 戦略ポイントをサークルとして表示
    mapInstance.addLayer({
      id: 'strategy-points-layer',
      type: 'circle',
      source: 'strategy-points',
      paint: {
        'circle-radius': 8,
        'circle-color': ['get', 'color'],
        'circle-opacity': 0.8,
        'circle-stroke-width': 2,
        'circle-stroke-color': '#ffffff',
      },
    });
    
    // ポップアップの追加
    mapInstance.on('click', 'strategy-points-layer', (e) => {
      const coordinates = e.features![0].geometry.coordinates.slice();
      const description = e.features![0].properties.description;
      
      // ポップアップを表示
      new maplibregl.Popup()
        .setLngLat(coordinates as [number, number])
        .setHTML(description)
        .addTo(mapInstance);
    });
    
    // カーソルスタイルの変更
    mapInstance.on('mouseenter', 'strategy-points-layer', () => {
      mapInstance.getCanvas().style.cursor = 'pointer';
    });
    
    mapInstance.on('mouseleave', 'strategy-points-layer', () => {
      mapInstance.getCanvas().style.cursor = '';
    });
  }, [strategyPoints, isMapLoaded, showStrategyPoints]);
  
  // 風速に応じた色を返す関数
  const getWindSpeedColor = (speed: number): string => {
    if (speed < 5) return '#85c4ff';  // 弱風: 薄い青
    if (speed < 10) return '#3498db'; // 中風: 青
    if (speed < 15) return '#2980b9'; // やや強風: 濃い青
    if (speed < 20) return '#e74c3c'; // 強風: 赤
    return '#c0392b';                 // 非常に強風: 濃い赤
  };
  
  // 戦略ポイントタイプに応じた色を返す関数
  const getStrategyPointColor = (type: string): string => {
    switch (type) {
      case 'tack': return '#e74c3c';      // タック: 赤
      case 'jibe': return '#3498db';      // ジャイブ: 青
      case 'wind_shift': return '#f39c12'; // 風向シフト: オレンジ
      case 'layline': return '#2ecc71';   // レイライン: 緑
      default: return '#95a5a6';          // その他: グレー
    }
  };
  
  // 戦略ポイントの説明を生成する関数
  const getStrategyPointDescription = (point: any): string => {
    const type = point.strategy_type;
    const timestamp = new Date(point.timestamp).toLocaleString();
    
    let description = `<strong>${getStrategyTypeName(type)}</strong><br>`;
    description += `時刻: ${timestamp}<br>`;
    description += `信頼度: ${(point.confidence * 100).toFixed(0)}%<br>`;
    
    // 戦略タイプに応じた追加情報
    if (type === 'wind_shift' && point.metadata) {
      description += `シフト角度: ${point.metadata.shift_angle.toFixed(1)}°<br>`;
      description += `変化前の風向: ${point.metadata.before_direction.toFixed(1)}°<br>`;
      description += `変化後の風向: ${point.metadata.after_direction.toFixed(1)}°<br>`;
    } else if (type === 'tack' && point.metadata) {
      description += `VMG利得: ${(point.metadata.vmg_gain * 100).toFixed(1)}%<br>`;
    } else if (type === 'layline' && point.metadata) {
      description += `マークID: ${point.metadata.mark_id}<br>`;
    }
    
    return description;
  };
  
  // 戦略タイプの日本語名を返す関数
  const getStrategyTypeName = (type: string): string => {
    switch (type) {
      case 'tack': return 'タック';
      case 'jibe': return 'ジャイブ';
      case 'wind_shift': return '風向シフト';
      case 'layline': return 'レイライン';
      default: return type;
    }
  };
  
  return (
    <div
      ref={mapContainer}
      style={{
        width: width,
        height: height,
        borderRadius: '4px',
        overflow: 'hidden',
      }}
    />
  );
};

export default MapView;