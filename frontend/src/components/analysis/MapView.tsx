import React, { useEffect, useRef, useState } from 'react';
import Map, { NavigationControl, Source, Layer, Popup } from 'react-map-gl/maplibre';
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
  const mapRef = useRef<any>(null);
  const [viewState, setViewState] = useState({
    longitude: 139.7, // デフォルト: 東京湾
    latitude: 35.7,
    zoom: 12
  });
  const [popupInfo, setPopupInfo] = useState<any>(null);

  // 初期表示位置の計算
  useEffect(() => {
    if (gpsData && gpsData.length > 0) {
      const lats = gpsData.map(point => point.latitude);
      const lons = gpsData.map(point => point.longitude);
      
      const minLat = Math.min(...lats);
      const maxLat = Math.max(...lats);
      const minLon = Math.min(...lons);
      const maxLon = Math.max(...lons);
      
      // 中心位置を設定
      setViewState({
        longitude: (minLon + maxLon) / 2,
        latitude: (minLat + maxLat) / 2,
        zoom: calculateZoomLevel(maxLat - minLat, maxLon - minLon)
      });
    }
  }, [gpsData]);
  
  // ズームレベルの計算（単純なヒューリスティック）
  const calculateZoomLevel = (latDiff: number, lonDiff: number): number => {
    const maxDiff = Math.max(latDiff, lonDiff);
    
    if (maxDiff > 0.1) return 10;
    if (maxDiff > 0.05) return 11;
    if (maxDiff > 0.01) return 13;
    return 14;
  };
  
  // GPSトラックのレイヤー設定
  const gpsTrackLayer = {
    id: 'gps-track-line',
    type: 'line',
    layout: {
      'line-join': 'round',
      'line-cap': 'round'
    },
    paint: {
      'line-color': '#0080ff',
      'line-width': 3
    }
  };
  
  // GPSトラックのGeoJSONデータ
  const gpsTrackData = {
    type: 'Feature',
    properties: {},
    geometry: {
      type: 'LineString',
      coordinates: gpsData.map(point => [point.longitude, point.latitude])
    }
  };
  
  // 風データのGeoJSONデータ
  const windDataFeatures = windData.map(point => ({
    type: 'Feature',
    properties: {
      direction: point.direction,
      speed: point.speed,
      color: getWindSpeedColor(point.speed)
    },
    geometry: {
      type: 'Point',
      coordinates: [point.longitude, point.latitude]
    }
  }));
  
  // 戦略ポイントのGeoJSONデータ
  const strategyPointFeatures = strategyPoints.map(point => ({
    type: 'Feature',
    properties: {
      type: point.strategy_type,
      confidence: point.confidence,
      color: getStrategyPointColor(point.strategy_type),
      description: getStrategyPointDescription(point),
      id: point.id || Math.random().toString(36).substr(2, 9)
    },
    geometry: {
      type: 'Point',
      coordinates: [point.longitude, point.latitude]
    }
  }));

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
  
  // 戦略ポイントのクリックハンドラ
  const handleStrategyPointClick = (event: any) => {
    if (event.features && event.features.length > 0) {
      const feature = event.features[0];
      setPopupInfo({
        longitude: event.lngLat.lng,
        latitude: event.lngLat.lat,
        description: feature.properties.description
      });
    }
  };
  
  return (
    <div style={{ width, height, borderRadius: '4px', overflow: 'hidden' }}>
      <Map
        ref={mapRef}
        {...viewState}
        onMove={evt => setViewState(evt.viewState)}
        mapStyle="https://demotiles.maplibre.org/style.json"
        style={{ width: '100%', height: '100%' }}
        interactiveLayerIds={showStrategyPoints ? ['strategy-points-layer'] : []}
        onClick={handleStrategyPointClick}
      >
        <NavigationControl position="top-right" />
        
        {/* GPSトラックの表示 */}
        {gpsData.length > 0 && (
          <Source id="gps-track" type="geojson" data={gpsTrackData as any}>
            <Layer {...gpsTrackLayer as any} />
          </Source>
        )}
        
        {/* 風データの表示 */}
        {showWindLayer && windData.length > 0 && (
          <Source
            id="wind-data"
            type="geojson"
            data={{
              type: 'FeatureCollection',
              features: windDataFeatures
            }}
          >
            <Layer
              id="wind-direction"
              type="circle"
              paint={{
                'circle-radius': 5,
                'circle-color': ['get', 'color'],
                'circle-opacity': 0.7
              }}
            />
          </Source>
        )}
        
        {/* 戦略ポイントの表示 */}
        {showStrategyPoints && strategyPoints.length > 0 && (
          <Source
            id="strategy-points"
            type="geojson"
            data={{
              type: 'FeatureCollection',
              features: strategyPointFeatures
            }}
          >
            <Layer
              id="strategy-points-layer"
              type="circle"
              paint={{
                'circle-radius': 8,
                'circle-color': ['get', 'color'],
                'circle-opacity': 0.8,
                'circle-stroke-width': 2,
                'circle-stroke-color': '#ffffff'
              }}
            />
          </Source>
        )}
        
        {/* ポップアップの表示 */}
        {popupInfo && (
          <Popup
            longitude={popupInfo.longitude}
            latitude={popupInfo.latitude}
            anchor="bottom"
            closeOnClick={true}
            onClose={() => setPopupInfo(null)}
          >
            <div dangerouslySetInnerHTML={{ __html: popupInfo.description }} />
          </Popup>
        )}
      </Map>
    </div>
  );
};

export default MapView;