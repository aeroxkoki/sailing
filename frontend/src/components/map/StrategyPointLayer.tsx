import React, { useEffect, useState } from 'react';
import mapboxgl from 'mapbox-gl';

export type StrategyPointType = 'tack' | 'gybe' | 'mark' | 'start' | 'finish' | 'custom';

interface StrategyPoint {
  id: string | number;
  longitude: number;
  latitude: number;
  type: StrategyPointType;
  timestamp?: number;
  quality?: number; // 0-1, represents the quality/confidence of the strategy point
  details?: {
    name?: string;
    description?: string;
    [key: string]: any;
  };
}

interface StrategyPointLayerProps {
  map: mapboxgl.Map;
  strategyPoints: StrategyPoint[];
  onPointClick?: (pointId: string | number) => void;
  selectedPoint?: string | number;
  showLabels?: boolean;
}

const StrategyPointLayer: React.FC<StrategyPointLayerProps> = ({
  map,
  strategyPoints,
  onPointClick,
  selectedPoint,
  showLabels = true,
}) => {
  const [sourceId] = useState(`strategy-source-${Math.random().toString(36).substring(2, 9)}`);
  const [pointsLayerId] = useState(`strategy-points-layer-${Math.random().toString(36).substring(2, 9)}`);
  const [labelsLayerId] = useState(`strategy-labels-layer-${Math.random().toString(36).substring(2, 9)}`);
  const [selectedSourceId] = useState(`selected-strategy-source-${Math.random().toString(36).substring(2, 9)}`);
  const [selectedLayerId] = useState(`selected-strategy-layer-${Math.random().toString(36).substring(2, 9)}`);

  // Set up custom markers for strategy points
  useEffect(() => {
    if (!map) return;

    const icons = {
      tack: {
        color: '#4CAF50',
        shape: 'triangle',
      },
      gybe: {
        color: '#2196F3',
        shape: 'circle',
      },
      mark: {
        color: '#F44336',
        shape: 'square',
      },
      start: {
        color: '#9C27B0',
        shape: 'diamond',
      },
      finish: {
        color: '#FF9800',
        shape: 'star',
      },
      custom: {
        color: '#795548',
        shape: 'pentagon',
      },
    };

    // Create custom marker icons
    Object.entries(icons).forEach(([type, { color, shape }]) => {
      const iconId = `strategy-icon-${type}`;
      
      if (!map.hasImage(iconId)) {
        const canvas = document.createElement('canvas');
        canvas.width = 24;
        canvas.height = 24;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        // Clear canvas
        ctx.clearRect(0, 0, 24, 24);
        
        // Draw shape
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
            // 5-pointed star
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
        
        // Fill and stroke
        ctx.fill();
        ctx.stroke();
        
        // canvas要素からImageDataを取得
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        
        // ImageDataオブジェクトを使って、Mapbox GLが期待するフォーマットでオブジェクトを作成
        const imageObject = {
          width: canvas.width,
          height: canvas.height,
          data: new Uint8Array(imageData.data.buffer)
        };
        
        // 準備したオブジェクトを使ってアイコンを登録
        map.addImage(iconId, imageObject);
      }
    });
  }, [map]);

  // Convert strategy points to GeoJSON
  const getStrategyPointsGeoJSON = () => {
    if (!strategyPoints || strategyPoints.length === 0) return null;

    return {
      type: 'FeatureCollection',
      features: strategyPoints.map(point => ({
        type: 'Feature',
        properties: {
          id: point.id,
          type: point.type,
          timestamp: point.timestamp,
          quality: point.quality || 1,
          name: point.details?.name || getDefaultName(point.type),
          description: point.details?.description || '',
          ...point.details,
        },
        geometry: {
          type: 'Point',
          coordinates: [point.longitude, point.latitude],
        },
      })),
    };
  };

  // Get selected point GeoJSON
  const getSelectedPointGeoJSON = () => {
    if (selectedPoint === undefined) return null;
    
    const point = strategyPoints.find(p => p.id === selectedPoint);
    if (!point) return null;
    
    return {
      type: 'Feature',
      properties: {
        id: point.id,
        type: point.type,
      },
      geometry: {
        type: 'Point',
        coordinates: [point.longitude, point.latitude],
      },
    };
  };

  // Utility for default names based on type
  const getDefaultName = (type: StrategyPointType) => {
    switch (type) {
      case 'tack': return 'タック';
      case 'gybe': return 'ジャイブ';
      case 'mark': return 'マーク';
      case 'start': return 'スタート';
      case 'finish': return 'フィニッシュ';
      case 'custom': return 'カスタムポイント';
      default: return 'ポイント';
    }
  };

  // Initialize and update layers
  useEffect(() => {
    if (!map || !strategyPoints || strategyPoints.length === 0) return;

    // Add strategy points source and layer
    if (!map.getSource(sourceId)) {
      map.addSource(sourceId, {
        type: 'geojson',
        data: getStrategyPointsGeoJSON() as any,
      });

      // Add strategy points layer
      map.addLayer({
        id: pointsLayerId,
        type: 'symbol',
        source: sourceId,
        layout: {
          'icon-image': ['concat', 'strategy-icon-', ['get', 'type']],
          'icon-size': ['interpolate', ['linear'], ['get', 'quality'], 
            0, 0.5,
            0.5, 0.75,
            1, 1.0
          ],
          'icon-allow-overlap': true,
        },
      });

      // Add labels if enabled
      if (showLabels) {
        map.addLayer({
          id: labelsLayerId,
          type: 'symbol',
          source: sourceId,
          layout: {
            'text-field': ['get', 'name'],
            'text-font': ['Open Sans Regular'],
            'text-size': 12,
            'text-offset': [0, 1.5],
            'text-anchor': 'top',
            'text-allow-overlap': false,
          },
          paint: {
            'text-color': '#333333',
            'text-halo-color': '#ffffff',
            'text-halo-width': 1,
          },
        });
      }

      // Add click handler
      if (onPointClick) {
        map.on('click', pointsLayerId, (e) => {
          if (e.features && e.features.length > 0) {
            const feature = e.features[0];
            const id = feature.properties?.id;
            if (id !== undefined) {
              onPointClick(id);
            }
          }
        });

        // Change cursor on hover
        map.on('mouseenter', pointsLayerId, () => {
          map.getCanvas().style.cursor = 'pointer';
        });

        map.on('mouseleave', pointsLayerId, () => {
          map.getCanvas().style.cursor = '';
        });
      }
    } else {
      // Update existing source
      const source = map.getSource(sourceId) as mapboxgl.GeoJSONSource;
      source.setData(getStrategyPointsGeoJSON() as any);
    }

    // Handle selected point
    if (selectedPoint !== undefined) {
      if (!map.getSource(selectedSourceId)) {
        map.addSource(selectedSourceId, {
          type: 'geojson',
          data: getSelectedPointGeoJSON() as any,
        });

        map.addLayer({
          id: selectedLayerId,
          type: 'circle',
          source: selectedSourceId,
          paint: {
            'circle-radius': 15,
            'circle-color': 'rgba(255, 255, 255, 0)',
            'circle-stroke-width': 3,
            'circle-stroke-color': '#000000',
          },
        });
      } else {
        // Update existing selected point source
        const source = map.getSource(selectedSourceId) as mapboxgl.GeoJSONSource;
        source.setData(getSelectedPointGeoJSON() as any);
      }
    }

    // Cleanup on unmount
    return () => {
      if (map.getLayer(pointsLayerId)) map.removeLayer(pointsLayerId);
      if (showLabels && map.getLayer(labelsLayerId)) map.removeLayer(labelsLayerId);
      if (map.getSource(sourceId)) map.removeSource(sourceId);
      if (map.getLayer(selectedLayerId)) map.removeLayer(selectedLayerId);
      if (map.getSource(selectedSourceId)) map.removeSource(selectedSourceId);
    };
  }, [
    map,
    strategyPoints,
    sourceId,
    pointsLayerId,
    labelsLayerId,
    selectedSourceId,
    selectedLayerId,
    selectedPoint,
    showLabels,
    onPointClick,
  ]);

  return null; // This component doesn't render anything on its own
};

export default StrategyPointLayer;