import React, { useEffect, useState } from 'react';
import maplibregl from 'maplibre-gl';

interface GridLayerProps {
  map: maplibregl.Map;
  visible: boolean;
  gridSize?: number; // グリッドサイズ（キロメートル）
  color?: string;
  lineWidth?: number;
}

const GridLayer: React.FC<GridLayerProps> = ({
  map,
  visible = true,
  gridSize = 1, // デフォルト1km
  color = 'rgba(255, 255, 255, 0.2)',
  lineWidth = 1,
}) => {
  const [sourceId] = useState(`grid-source-${Math.random().toString(36).substring(2, 9)}`);
  const [layerId] = useState(`grid-layer-${Math.random().toString(36).substring(2, 9)}`);

  // 緯度経度のグリッドを生成
  const generateGrid = (bounds: maplibregl.LngLatBounds, gridStepKm: number) => {
    // グリッドのGeoJSONライン機能の配列
    const lines: GeoJSON.Feature<GeoJSON.LineString>[] = [];
    
    // 緯度1度は約111km、経度1度は緯度によって変化
    const latStep = gridStepKm / 111; // km to degrees for latitude
    
    // 中心点の緯度を使用して経度のステップを計算
    const centerLat = bounds.getCenter().lat;
    // 経度の1度の距離は緯度によって変わる (約111 * cos(lat) km)
    const lngStep = gridStepKm / (111 * Math.cos(centerLat * Math.PI / 180));
    
    // 境界を少し拡張して、グリッドが画面外までカバーするようにする
    const extendedBounds = new maplibregl.LngLatBounds(
      [bounds.getWest() - lngStep, bounds.getSouth() - latStep],
      [bounds.getEast() + lngStep, bounds.getNorth() + latStep]
    );
    
    // ステップごとに緯度線（東西方向の線）を生成
    for (
      let lat = Math.floor(extendedBounds.getSouth() / latStep) * latStep;
      lat <= extendedBounds.getNorth();
      lat += latStep
    ) {
      lines.push({
        type: 'Feature',
        properties: { isLatitude: true, value: lat },
        geometry: {
          type: 'LineString',
          coordinates: [
            [extendedBounds.getWest(), lat],
            [extendedBounds.getEast(), lat],
          ],
        },
      });
    }
    
    // ステップごとに経度線（南北方向の線）を生成
    for (
      let lng = Math.floor(extendedBounds.getWest() / lngStep) * lngStep;
      lng <= extendedBounds.getEast();
      lng += lngStep
    ) {
      lines.push({
        type: 'Feature',
        properties: { isLatitude: false, value: lng },
        geometry: {
          type: 'LineString',
          coordinates: [
            [lng, extendedBounds.getSouth()],
            [lng, extendedBounds.getNorth()],
          ],
        },
      });
    }
    
    return {
      type: 'FeatureCollection',
      features: lines,
    };
  };

  // グリッドレイヤーの作成と更新
  useEffect(() => {
    if (!map) return;

    // 表示が無効な場合はレイヤーを削除
    if (!visible) {
      if (map.getLayer(layerId)) {
        map.removeLayer(layerId);
      }
      if (map.getSource(sourceId)) {
        map.removeSource(sourceId);
      }
      return;
    }

    // 現在の地図の境界を取得
    const bounds = map.getBounds();
    
    // グリッドのGeoJSONを生成
    const gridGeoJSON = generateGrid(bounds, gridSize);

    // ソースとレイヤーの追加または更新
    if (!map.getSource(sourceId)) {
      map.addSource(sourceId, {
        type: 'geojson',
        data: gridGeoJSON as any,
      });

      map.addLayer({
        id: layerId,
        type: 'line',
        source: sourceId,
        layout: {
          'line-join': 'round',
          'line-cap': 'round',
        },
        paint: {
          'line-color': color,
          'line-width': lineWidth,
        },
      });
    } else {
      // 既存ソースの更新
      const source = map.getSource(sourceId) as maplibregl.GeoJSONSource;
      source.setData(gridGeoJSON as any);
      
      // スタイルの更新
      map.setPaintProperty(layerId, 'line-color', color);
      map.setPaintProperty(layerId, 'line-width', lineWidth);
    }

    // 地図の移動や拡大縮小時にグリッドを更新
    const updateGrid = () => {
      if (map.getSource(sourceId)) {
        const bounds = map.getBounds();
        const gridGeoJSON = generateGrid(bounds, gridSize);
        const source = map.getSource(sourceId) as maplibregl.GeoJSONSource;
        source.setData(gridGeoJSON as any);
      }
    };

    map.on('move', updateGrid);
    map.on('zoom', updateGrid);

    // クリーンアップ関数
    return () => {
      map.off('move', updateGrid);
      map.off('zoom', updateGrid);
      
      if (map.getLayer(layerId)) {
        map.removeLayer(layerId);
      }
      if (map.getSource(sourceId)) {
        map.removeSource(sourceId);
      }
    };
  }, [map, visible, gridSize, color, lineWidth, sourceId, layerId]);

  return null; // このコンポーネントは直接UIを描画しない
};

export default GridLayer;
