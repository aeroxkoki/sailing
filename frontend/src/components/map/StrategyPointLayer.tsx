import React, { useEffect, useState, useCallback } from 'react';
import maplibregl from 'maplibre-gl';
import { StrategyPoint, StrategyPointType } from '@/types/gps';

interface StrategyPointLayerProps {
  map: maplibregl.Map;
  strategyPoints: StrategyPoint[];
  selectedTime?: number;
  timeWindow?: number; // ミリ秒単位の時間ウィンドウ
  showLabels?: boolean;
  onPointClick?: (point: StrategyPoint) => void;
}

const StrategyPointLayer: React.FC<StrategyPointLayerProps> = ({
  map,
  strategyPoints,
  selectedTime,
  timeWindow = 600000, // デフォルト10分
  showLabels = true,
  onPointClick,
}) => {
  const [sourceId] = useState(`strategy-source-${Math.random().toString(36).substring(2, 9)}`);
  const [pointsLayerId] = useState(`strategy-points-layer-${Math.random().toString(36).substring(2, 9)}`);
  const [labelsLayerId] = useState(`strategy-labels-layer-${Math.random().toString(36).substring(2, 9)}`);
  const [currentPointSourceId] = useState(`current-strategy-source-${Math.random().toString(36).substring(2, 9)}`);
  const [currentPointLayerId] = useState(`current-strategy-layer-${Math.random().toString(36).substring(2, 9)}`);

  // 現在の時間ウィンドウに基づいて戦略ポイントをフィルタリング
  const getFilteredStrategyPoints = useCallback(() => {
    if (selectedTime === undefined || !timeWindow) {
      return strategyPoints;
    }

    return strategyPoints.filter(point => {
      const diff = Math.abs(point.timestamp - selectedTime);
      return diff <= timeWindow / 2;
    });
  }, [strategyPoints, selectedTime, timeWindow]);

  // 戦略ポイント用の独自マーカーアイコンを設定
  useEffect(() => {
    if (!map) return;

    const icons = {
      [StrategyPointType.TACK]: {
        color: '#4CAF50', // 緑
        shape: 'triangle',
      },
      [StrategyPointType.JIBE]: {
        color: '#2196F3', // 青
        shape: 'circle',
      },
      [StrategyPointType.MARK_ROUNDING]: {
        color: '#F44336', // 赤
        shape: 'square',
      },
      [StrategyPointType.WIND_SHIFT]: {
        color: '#9C27B0', // 紫
        shape: 'diamond',
      },
      [StrategyPointType.LAYLINE]: {
        color: '#FF9800', // オレンジ
        shape: 'pentagon',
      },
      [StrategyPointType.START]: {
        color: '#009688', // ティール
        shape: 'star',
      },
      [StrategyPointType.FINISH]: {
        color: '#795548', // 茶色
        shape: 'star',
      },
    };

    // カスタムマーカーアイコンを作成
    Object.entries(icons).forEach(([type, { color, shape }]) => {
      const iconId = `strategy-icon-${type}`;
      
      if (!map.hasImage(iconId)) {
        const canvas = document.createElement('canvas');
        canvas.width = 24;
        canvas.height = 24;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        // キャンバスをクリア
        ctx.clearRect(0, 0, 24, 24);
        
        // 形を描画
        ctx.fillStyle = color;
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 2;
        
        switch (shape) {
          case 'triangle':
            ctx.beginPath();
            ctx.moveTo(12, 2);
            ctx.lineTo(22, 22);
            ctx.lineTo(2, 22);
            ctx.closePath();
            break;
          case 'circle':
            ctx.beginPath();
            ctx.arc(12, 12, 10, 0, Math.PI * 2);
            ctx.closePath();
            break;
          case 'square':
            ctx.beginPath();
            ctx.rect(2, 2, 20, 20);
            ctx.closePath();
            break;
          case 'diamond':
            ctx.beginPath();
            ctx.moveTo(12, 2);
            ctx.lineTo(22, 12);
            ctx.lineTo(12, 22);
            ctx.lineTo(2, 12);
            ctx.closePath();
            break;
          case 'star':
            // 5つ星
            ctx.beginPath();
            for (let i = 0; i < 5; i++) {
              const outerAngle = i * Math.PI * 2 / 5 - Math.PI / 2;
              const innerAngle = outerAngle + Math.PI / 5;
              
              const outerX = 12 + 10 * Math.cos(outerAngle);
              const outerY = 12 + 10 * Math.sin(outerAngle);
              
              const innerX = 12 + 4 * Math.cos(innerAngle);
              const innerY = 12 + 4 * Math.sin(innerAngle);
              
              if (i === 0) {
                ctx.moveTo(outerX, outerY);
              } else {
                ctx.lineTo(outerX, outerY);
              }
              
              ctx.lineTo(innerX, innerY);
            }
            ctx.closePath();
            break;
          case 'pentagon':
            ctx.beginPath();
            for (let i = 0; i < 5; i++) {
              const angle = i * Math.PI * 2 / 5 - Math.PI / 2;
              const x = 12 + 10 * Math.cos(angle);
              const y = 12 + 10 * Math.sin(angle);
              
              if (i === 0) {
                ctx.moveTo(x, y);
              } else {
                ctx.lineTo(x, y);
              }
            }
            ctx.closePath();
            break;
          default:
            ctx.beginPath();
            ctx.arc(12, 12, 10, 0, Math.PI * 2);
            ctx.closePath();
        }
        
        // 塗りつぶしと枠線
        ctx.fill();
        ctx.stroke();
        
        // キャンバスから画像データを取得
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        map.addImage(iconId, imageData);
      }
    });
  }, [map]);

  // ポイント名を取得
  const getPointName = useCallback((point: StrategyPoint): string => {
    if (point.details?.name) return point.details.name;
    
    // タイプに基づくデフォルト名
    switch (point.type) {
      case StrategyPointType.TACK: return 'タック';
      case StrategyPointType.JIBE: return 'ジャイブ';
      case StrategyPointType.MARK_ROUNDING: return 'マーク回航';
      case StrategyPointType.WIND_SHIFT: return '風向シフト';
      case StrategyPointType.LAYLINE: return 'レイライン';
      case StrategyPointType.START: return 'スタート';
      case StrategyPointType.FINISH: return 'フィニッシュ';
      default: return '戦略ポイント';
    }
  }, []);

  // ポイント説明を取得
  const getPointDescription = useCallback((point: StrategyPoint): string => {
    // 評価コメントがある場合はそれを使用
    if (point.evaluation?.comments) return point.evaluation.comments;
    
    // 詳細説明がある場合はそれを使用
    if (point.details?.description) return point.details.description;
    
    // デフォルトの説明
    return '';
  }, []);

  // getStrategyPointsGeoJSON の依存配列を更新
  const getStrategyPointsGeoJSON = useCallback(() => {
    const filteredPoints = getFilteredStrategyPoints();
    if (!filteredPoints || filteredPoints.length === 0) return null;

    return {
      type: 'FeatureCollection',
      features: filteredPoints.map(point => ({
        type: 'Feature',
        properties: {
          id: point.id,
          type: point.type,
          timestamp: point.timestamp,
          score: point.evaluation?.score || 1,
          name: getPointName(point),
          description: getPointDescription(point),
          details: JSON.stringify(point.details || {}),
          evaluation: JSON.stringify(point.evaluation || {}),
        },
        geometry: {
          type: 'Point',
          coordinates: [point.longitude, point.latitude],
        },
      })),
    };
  }, [getFilteredStrategyPoints, getPointName, getPointDescription]);

  // 現在時間に最も近い戦略ポイントを取得
  const getCurrentStrategyPointGeoJSON = useCallback(() => {
    if (!selectedTime || !strategyPoints || strategyPoints.length === 0) return null;

    // 選択時間に最も近いポイントを見つける
    let closestPoint = strategyPoints[0];
    let minDiff = Math.abs(closestPoint.timestamp - selectedTime);

    strategyPoints.forEach(point => {
      const diff = Math.abs(point.timestamp - selectedTime);
      if (diff < minDiff) {
        closestPoint = point;
        minDiff = diff;
      }
    });

    // 時間差があまりに大きい場合は表示しない
    if (minDiff > 5000) return null; // 5秒以上離れていたら表示しない

    return {
      type: 'Feature',
      properties: {
        id: closestPoint.id,
        type: closestPoint.type,
      },
      geometry: {
        type: 'Point',
        coordinates: [closestPoint.longitude, closestPoint.latitude],
      },
    };
  }, [strategyPoints, selectedTime]);

  // レイヤーの初期化と更新
  useEffect(() => {
    if (!map || !strategyPoints || strategyPoints.length === 0) return;

    // 戦略ポイントのソースとレイヤーを追加
    if (!map.getSource(sourceId)) {
      map.addSource(sourceId, {
        type: 'geojson',
        data: getStrategyPointsGeoJSON() as any,
      });

      // 戦略ポイントレイヤーを追加
      map.addLayer({
        id: pointsLayerId,
        type: 'symbol',
        source: sourceId,
        layout: {
          'icon-image': ['concat', 'strategy-icon-', ['get', 'type']],
          'icon-size': ['interpolate', ['linear'], ['get', 'score'], 
            0, 0.5,    // 低評価は小さく
            0.5, 0.75, // 中評価は中くらい
            1, 1.0     // 高評価は標準サイズ
          ],
          'icon-allow-overlap': true,
        },
      });

      // ラベルを追加（オプション）
      if (showLabels) {
        map.addLayer({
          id: labelsLayerId,
          type: 'symbol',
          source: sourceId,
          layout: {
            'text-field': ['get', 'name'],
            'text-size': 12,
            'text-offset': [0, 1.5],
            'text-anchor': 'top',
            'text-allow-overlap': false,
          },
          paint: {
            'text-color': '#ffffff',
            'text-halo-color': '#000000',
            'text-halo-width': 1,
          },
        });
      }

      // クリックハンドラを追加
      if (onPointClick) {
        map.on('click', pointsLayerId, (e) => {
          if (e.features && e.features.length > 0) {
            const id = e.features[0].properties?.id;
            if (id !== undefined) {
              const point = strategyPoints.find(p => p.id === id);
              if (point) {
                onPointClick(point);
              }
            }
          }
        });

        // ホバー時のカーソル変更
        map.on('mouseenter', pointsLayerId, () => {
          map.getCanvas().style.cursor = 'pointer';
        });

        map.on('mouseleave', pointsLayerId, () => {
          map.getCanvas().style.cursor = '';
        });
      }
    } else {
      // 既存ソースのデータを更新
      const source = map.getSource(sourceId) as maplibregl.GeoJSONSource;
      source.setData(getStrategyPointsGeoJSON() as any);
    }

    // 現在時間に最も近いポイントの強調表示
    const currentPoint = getCurrentStrategyPointGeoJSON();
    if (currentPoint) {
      if (!map.getSource(currentPointSourceId)) {
        map.addSource(currentPointSourceId, {
          type: 'geojson',
          data: currentPoint as any,
        });

        map.addLayer({
          id: currentPointLayerId,
          type: 'circle',
          source: currentPointSourceId,
          paint: {
            'circle-radius': 15,
            'circle-color': 'rgba(255, 255, 255, 0)',
            'circle-stroke-width': 3,
            'circle-stroke-color': '#ffffff',
          },
        }, pointsLayerId); // 戦略ポイントレイヤーの下に配置
      } else {
        // 既存ソースのデータを更新
        const source = map.getSource(currentPointSourceId) as maplibregl.GeoJSONSource;
        source.setData(currentPoint as any);
      }
    } else {
      // 現在のポイントが存在しない場合はレイヤーを非表示にする
      if (map.getLayer(currentPointLayerId)) {
        if (map.getLayoutProperty(currentPointLayerId, 'visibility') !== 'none') {
          map.setLayoutProperty(currentPointLayerId, 'visibility', 'none');
        }
      }
    }

    // クリーンアップ関数
    return () => {
      if (map.getLayer(pointsLayerId)) map.removeLayer(pointsLayerId);
      if (showLabels && map.getLayer(labelsLayerId)) map.removeLayer(labelsLayerId);
      if (map.getSource(sourceId)) map.removeSource(sourceId);
      if (map.getLayer(currentPointLayerId)) map.removeLayer(currentPointLayerId);
      if (map.getSource(currentPointSourceId)) map.removeSource(currentPointSourceId);
    };
  }, [
    map,
    strategyPoints,
    sourceId,
    pointsLayerId,
    labelsLayerId,
    currentPointSourceId,
    currentPointLayerId,
    selectedTime,
    timeWindow,
    showLabels,
    onPointClick,
    getStrategyPointsGeoJSON,
    getCurrentStrategyPointGeoJSON
  ]);

  return null; // このコンポーネントは直接UIを描画しない
};

export default StrategyPointLayer;