import React, { useEffect, useState, useCallback } from 'react';
import maplibregl from 'maplibre-gl';
import { GpsPoint } from '@/types/gps';

interface TrackLayerProps {
  map: maplibregl.Map;
  trackData: GpsPoint[];
  colorScheme?: 'speed' | 'vmg' | 'heading';
  selectedTime?: number;
  timeWindow?: number; // ミリ秒単位の時間ウィンドウ
  lineWidth?: number;
  showPoints?: boolean;
  fitBounds?: boolean;
  onPointClick?: (point: GpsPoint) => void;
}

const TrackLayer: React.FC<TrackLayerProps> = ({
  map,
  trackData,
  colorScheme = 'speed',
  selectedTime,
  timeWindow = 60000, // デフォルト1分
  lineWidth = 3,
  showPoints = true,
  fitBounds = true,
  onPointClick,
}) => {
  const [sourceId] = useState(`track-source-${Math.random().toString(36).substring(2, 9)}`);
  const [layerId] = useState(`track-layer-${Math.random().toString(36).substring(2, 9)}`);
  const [pointsSourceId] = useState(`track-points-source-${Math.random().toString(36).substring(2, 9)}`);
  const [pointsLayerId] = useState(`track-points-layer-${Math.random().toString(36).substring(2, 9)}`);
  const [currentPointSourceId] = useState(`current-point-source-${Math.random().toString(36).substring(2, 9)}`);
  const [currentPointLayerId] = useState(`current-point-layer-${Math.random().toString(36).substring(2, 9)}`);

  // 現在の時間ウィンドウに基づいてGPSデータをフィルタリング
  const getFilteredTrackData = useCallback(() => {
    if (selectedTime === undefined || !timeWindow) {
      return trackData;
    }

    return trackData.filter(point => {
      const diff = Math.abs(point.timestamp - selectedTime);
      return diff <= timeWindow / 2;
    });
  }, [trackData, selectedTime, timeWindow]);

  // トラックラインのGeoJSONを生成
  const getTrackGeoJSON = useCallback(() => {
    if (!trackData || trackData.length === 0) return null;

    return {
      type: 'Feature',
      properties: {},
      geometry: {
        type: 'LineString',
        coordinates: trackData.map(point => [point.longitude, point.latitude]),
      },
    };
  }, [trackData]);

  // トラックポイントのGeoJSONを生成
  const getTrackPointsGeoJSON = useCallback(() => {
    if (!trackData || trackData.length === 0) return null;

    return {
      type: 'FeatureCollection',
      features: trackData.map((point, index) => ({
        type: 'Feature',
        properties: {
          id: index,
          timestamp: point.timestamp,
          speed: point.speed || 0,
          heading: point.heading || 0,
          // 選択された時間に近いポイントに属性を追加
          isSelected: selectedTime ? Math.abs(point.timestamp - selectedTime) < 100 : false,
        },
        geometry: {
          type: 'Point',
          coordinates: [point.longitude, point.latitude],
        },
      })),
    };
  }, [trackData, selectedTime]);

  // 現在の時間に対応するポイントのGeoJSONを生成
  const getCurrentPointGeoJSON = useCallback(() => {
    if (!selectedTime || !trackData || trackData.length === 0) return null;

    // 選択された時間に最も近いポイントを見つける
    let closestPoint = trackData[0];
    let minDiff = Math.abs(closestPoint.timestamp - selectedTime);

    trackData.forEach(point => {
      const diff = Math.abs(point.timestamp - selectedTime);
      if (diff < minDiff) {
        closestPoint = point;
        minDiff = diff;
      }
    });

    return {
      type: 'Feature',
      properties: {
        speed: closestPoint.speed || 0,
        heading: closestPoint.heading || 0,
      },
      geometry: {
        type: 'Point',
        coordinates: [closestPoint.longitude, closestPoint.latitude],
      },
    };
  }, [trackData, selectedTime]);

  // 色分けの式を取得
  const getColorExpression = useCallback((scheme: string): string | any[] => {
    switch (scheme) {
      case 'speed':
        return [
          'interpolate',
          ['linear'],
          ['get', 'speed'],
          0, '#3B82F6',  // 低速 - 青
          5, '#60A5FA',  // 中速 - 水色
          10, '#F59E0B', // 高速 - オレンジ
          15, '#EF4444'  // 最高速 - 赤
        ];
      case 'vmg':
        return [
          'interpolate',
          ['linear'],
          ['get', 'vmg'],
          0, '#3B82F6',   // 低VMG - 青
          3, '#10B981',   // 中VMG - 緑
          6, '#F59E0B',   // 高VMG - オレンジ
        ];
      case 'heading':
        return [
          'interpolate',
          ['linear'],
          ['get', 'heading'],
          0, '#3B82F6',    // 北 - 青
          90, '#10B981',   // 東 - 緑
          180, '#F59E0B',  // 南 - オレンジ
          270, '#EF4444',  // 西 - 赤
          360, '#3B82F6'   // 北 - 青
        ];
      default:
        return '#3B82F6';  // デフォルト青
    }
  }, []);

  // トラックレイヤーの初期化と更新
  useEffect(() => {
    if (!map || !trackData || trackData.length === 0) return;

    // トラックラインソースとレイヤーの追加
    if (!map.getSource(sourceId)) {
      map.addSource(sourceId, {
        type: 'geojson',
        data: getTrackGeoJSON() as any,
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
          'line-color': getColorExpression(colorScheme) as any,
          'line-width': lineWidth,
        },
      });
    } else {
      // 既存ソースのデータを更新
      const source = map.getSource(sourceId) as maplibregl.GeoJSONSource;
      source.setData(getTrackGeoJSON() as any);
      
      // 色分けスキームを更新
      map.setPaintProperty(layerId, 'line-color', getColorExpression(colorScheme) as any);
      map.setPaintProperty(layerId, 'line-width', lineWidth);
    }

    // トラックポイントの表示（オプション）
    if (showPoints) {
      if (!map.getSource(pointsSourceId)) {
        map.addSource(pointsSourceId, {
          type: 'geojson',
          data: getTrackPointsGeoJSON() as any,
        });

        map.addLayer({
          id: pointsLayerId,
          type: 'circle',
          source: pointsSourceId,
          paint: {
            'circle-radius': [
              'case',
              ['get', 'isSelected'],
              6, // 選択されたポイントは大きく
              3  // 通常のポイント
            ],
            'circle-color': getColorExpression(colorScheme) as any,
            'circle-stroke-color': '#ffffff',
            'circle-stroke-width': 1,
            'circle-opacity': [
              'case',
              ['get', 'isSelected'],
              1, // 選択されたポイントは完全に不透明
              0.7 // 通常のポイントは少し透明
            ],
          },
        });

        // クリックイベントの設定
        if (onPointClick) {
          map.on('click', pointsLayerId, (e) => {
            if (e.features && e.features.length > 0) {
              const id = e.features[0].properties?.id;
              if (id !== undefined && trackData[id]) {
                onPointClick(trackData[id]);
              }
            }
          });

          // ポインタの変更
          map.on('mouseenter', pointsLayerId, () => {
            map.getCanvas().style.cursor = 'pointer';
          });

          map.on('mouseleave', pointsLayerId, () => {
            map.getCanvas().style.cursor = '';
          });
        }
      } else {
        // 既存ソースのデータを更新
        const source = map.getSource(pointsSourceId) as maplibregl.GeoJSONSource;
        source.setData(getTrackPointsGeoJSON() as any);
      }
    } else {
      // ポイントレイヤーが不要な場合は削除
      if (map.getLayer(pointsLayerId)) {
        map.removeLayer(pointsLayerId);
      }
      if (map.getSource(pointsSourceId)) {
        map.removeSource(pointsSourceId);
      }
    }

    // 現在選択されているポイントを表示
    if (selectedTime) {
      if (!map.getSource(currentPointSourceId)) {
        map.addSource(currentPointSourceId, {
          type: 'geojson',
          data: getCurrentPointGeoJSON() as any,
        });

        map.addLayer({
          id: currentPointLayerId,
          type: 'circle',
          source: currentPointSourceId,
          paint: {
            'circle-radius': 8,
            'circle-color': '#ffffff',
            'circle-stroke-color': '#000000',
            'circle-stroke-width': 2,
          },
        });
      } else {
        // 既存ソースのデータを更新
        const source = map.getSource(currentPointSourceId) as maplibregl.GeoJSONSource;
        source.setData(getCurrentPointGeoJSON() as any);
      }
    }

    // マップの表示範囲をトラックに合わせる（初回のみ）
    if (fitBounds && trackData.length > 1) {
      const bounds = new maplibregl.LngLatBounds();
      trackData.forEach(point => {
        bounds.extend([point.longitude, point.latitude]);
      });

      map.fitBounds(bounds, {
        padding: { top: 50, bottom: 50, left: 50, right: 50 },
        animate: true,
        duration: 500,
      });
    }

    // クリーンアップ関数
    return () => {
      if (map.getLayer(layerId)) map.removeLayer(layerId);
      if (map.getSource(sourceId)) map.removeSource(sourceId);
      
      if (map.getLayer(pointsLayerId)) map.removeLayer(pointsLayerId);
      if (map.getSource(pointsSourceId)) map.removeSource(pointsSourceId);
      
      if (map.getLayer(currentPointLayerId)) map.removeLayer(currentPointLayerId);
      if (map.getSource(currentPointSourceId)) map.removeSource(currentPointSourceId);
    };
  }, [
    map,
    trackData,
    sourceId,
    layerId,
    pointsSourceId,
    pointsLayerId,
    currentPointSourceId,
    currentPointLayerId,
    colorScheme,
    selectedTime,
    lineWidth,
    showPoints,
    fitBounds,
    onPointClick,
    getTrackGeoJSON,
    getTrackPointsGeoJSON,
    getCurrentPointGeoJSON,
    getColorExpression
  ]);

  return null; // このコンポーネントは直接UIを描画しない
};

export default TrackLayer;