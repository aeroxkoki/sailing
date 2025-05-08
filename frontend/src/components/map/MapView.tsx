import React, { useRef, useEffect, useState } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

interface MapViewProps {
  center?: [number, number]; // [longitude, latitude]
  zoom?: number;
  style?: 'dark' | 'satellite' | 'nautical';
  width?: string;
  height?: string;
  className?: string;
  onMapLoaded?: (map: maplibregl.Map) => void;
  children?: React.ReactNode;
}

const MapView: React.FC<MapViewProps> = ({
  center = [139.767, 35.681], // Tokyo by default
  zoom = 12,
  style = 'dark',
  width = '100%',
  height = '500px',
  className = '',
  onMapLoaded,
  children,
}) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  
  useEffect(() => {
    if (!mapContainer.current) return;
    
    // マップスタイルURL
    const styleUrls = {
      dark: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
      satellite: 'https://api.maptiler.com/maps/hybrid/style.json?key=YOUR_KEY',
      nautical: 'https://api.maptiler.com/maps/ocean/style.json?key=YOUR_KEY'
    };
    
    // MapLibre GL JS の初期化
    const mapInstance = new maplibregl.Map({
      container: mapContainer.current,
      style: styleUrls[style],
      center: center,
      zoom: zoom,
    });
    
    // ナビゲーションコントロールの追加
    mapInstance.addControl(new maplibregl.NavigationControl(), 'top-right');
    
    // スケールコントロールの追加
    mapInstance.addControl(
      new maplibregl.ScaleControl({ maxWidth: 80, unit: 'metric' }),
      'bottom-left'
    );
    
    // マップ読み込み完了イベント
    mapInstance.on('load', () => {
      setMapLoaded(true);
      if (onMapLoaded) onMapLoaded(mapInstance);
    });
    
    // クリーンアップ
    map.current = mapInstance;
    return () => {
      mapInstance.remove();
      map.current = null;
    };
  }, [center, zoom, style, onMapLoaded]);
  
  // マップコンテキストを子コンポーネントに公開
  const mapContext = {
    map: map.current,
    mapLoaded,
  };
  
  return (
    <div 
      className={`relative overflow-hidden rounded-lg ${className}`}
      style={{ width, height }}
    >
      <div ref={mapContainer} className="absolute inset-0" />
      {mapLoaded && children}
    </div>
  );
};

export default MapView;