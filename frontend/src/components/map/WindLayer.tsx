import React, { useEffect, useState } from 'react';
import mapboxgl from 'mapbox-gl';

interface WindPoint {
  longitude: number;
  latitude: number;
  direction: number; // in degrees, 0 = North, 90 = East, etc.
  speed: number; // in knots
  timestamp?: number;
}

interface WindLayerProps {
  map: mapboxgl.Map;
  windPoints: WindPoint[];
  vectorColor?: string;
  vectorScale?: number;
  showHeatmap?: boolean;
  heatmapOpacity?: number;
  heatmapRadius?: number;
  selectedTime?: number;
  timeWindow?: number; // time window in milliseconds
}

const WindLayer: React.FC<WindLayerProps> = ({
  map,
  windPoints,
  vectorColor = '#48cae4',
  vectorScale = 0.5,
  showHeatmap = true,
  heatmapOpacity = 0.6,
  heatmapRadius = 30,
  selectedTime,
  timeWindow = 300000, // 5 minutes by default
}) => {
  const [vectorSourceId] = useState(`wind-vector-source-${Math.random().toString(36).substring(2, 9)}`);
  const [vectorLayerId] = useState(`wind-vector-layer-${Math.random().toString(36).substring(2, 9)}`);
  const [heatmapSourceId] = useState(`wind-heatmap-source-${Math.random().toString(36).substring(2, 9)}`);
  const [heatmapLayerId] = useState(`wind-heatmap-layer-${Math.random().toString(36).substring(2, 9)}`);

  // Filter wind points by time if needed
  const getFilteredWindPoints = () => {
    if (selectedTime === undefined || !timeWindow) {
      return windPoints;
    }

    return windPoints.filter(point => {
      if (!point.timestamp) return true;
      const diff = Math.abs(point.timestamp - selectedTime);
      return diff <= timeWindow / 2;
    });
  };

  // Convert wind points to GeoJSON for vectors
  const getWindVectorsGeoJSON = () => {
    const filteredPoints = getFilteredWindPoints();
    if (!filteredPoints || filteredPoints.length === 0) return null;

    return {
      type: 'FeatureCollection',
      features: filteredPoints.map(point => ({
        type: 'Feature',
        properties: {
          direction: point.direction,
          speed: point.speed,
          timestamp: point.timestamp,
        },
        geometry: {
          type: 'Point',
          coordinates: [point.longitude, point.latitude],
        },
      })),
    };
  };

  // Convert wind points to GeoJSON for heatmap
  const getWindHeatmapGeoJSON = () => {
    const filteredPoints = getFilteredWindPoints();
    if (!filteredPoints || filteredPoints.length === 0) return null;

    return {
      type: 'FeatureCollection',
      features: filteredPoints.map(point => ({
        type: 'Feature',
        properties: {
          speed: point.speed,
        },
        geometry: {
          type: 'Point',
          coordinates: [point.longitude, point.latitude],
        },
      })),
    };
  };

  // Create wind arrow images
  useEffect(() => {
    if (!map || !map.hasImage('wind-arrow')) {
      const canvas = document.createElement('canvas');
      canvas.width = 40;
      canvas.height = 40;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      // Clear canvas
      ctx.clearRect(0, 0, 40, 40);

      // Draw arrow pointing north
      ctx.fillStyle = 'rgba(0, 0, 0, 0)';
      ctx.fillRect(0, 0, 40, 40);
      ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
      ctx.strokeStyle = vectorColor;
      ctx.lineWidth = 2;

      // Arrow shape
      ctx.beginPath();
      ctx.moveTo(20, 5); // Top
      ctx.lineTo(15, 20); // Bottom left
      ctx.lineTo(20, 15); // Bottom middle
      ctx.lineTo(25, 20); // Bottom right
      ctx.closePath();
      ctx.fill();
      ctx.stroke();

      // Shaft
      ctx.beginPath();
      ctx.moveTo(20, 15);
      ctx.lineTo(20, 30);
      ctx.stroke();

      map.addImage('wind-arrow', canvas, { sdf: true });
    }
  }, [map, vectorColor]);

  // Initialize and update wind layers
  useEffect(() => {
    if (!map) return;

    // Create and update vector layer
    if (!map.getSource(vectorSourceId)) {
      map.addSource(vectorSourceId, {
        type: 'geojson',
        data: getWindVectorsGeoJSON() as any,
      });

      map.addLayer({
        id: vectorLayerId,
        type: 'symbol',
        source: vectorSourceId,
        layout: {
          'icon-image': 'wind-arrow',
          'icon-size': ['interpolate', ['linear'], ['get', 'speed'], 
            0, 0.5,
            10, 0.75,
            20, 1.0,
            30, 1.25
          ],
          'icon-rotate': ['get', 'direction'],
          'icon-allow-overlap': true,
          'icon-anchor': 'center',
          'symbol-sort-key': ['get', 'speed'],
        },
        paint: {
          'icon-color': vectorColor,
          'icon-opacity': 0.8,
        },
      });
    } else if (map.getSource(vectorSourceId)) {
      const source = map.getSource(vectorSourceId) as mapboxgl.GeoJSONSource;
      source.setData(getWindVectorsGeoJSON() as any);
    }

    // Create and update heatmap layer if enabled
    if (showHeatmap) {
      if (!map.getSource(heatmapSourceId)) {
        map.addSource(heatmapSourceId, {
          type: 'geojson',
          data: getWindHeatmapGeoJSON() as any,
        });

        map.addLayer({
          id: heatmapLayerId,
          type: 'heatmap',
          source: heatmapSourceId,
          paint: {
            'heatmap-weight': ['interpolate', ['linear'], ['get', 'speed'], 
              0, 0,
              10, 0.5,
              20, 0.8,
              30, 1
            ],
            'heatmap-intensity': 1,
            'heatmap-color': [
              'interpolate',
              ['linear'],
              ['heatmap-density'],
              0, 'rgba(0, 0, 255, 0)',
              0.2, 'rgba(0, 255, 255, 0.3)',
              0.4, 'rgba(0, 255, 0, 0.5)',
              0.6, 'rgba(255, 255, 0, 0.7)',
              0.8, 'rgba(255, 128, 0, 0.8)',
              1, 'rgba(255, 0, 0, 0.9)'
            ],
            'heatmap-radius': heatmapRadius,
            'heatmap-opacity': heatmapOpacity,
          },
        }, 'wind-vector-layer'); // Add heatmap below vector layer
      } else if (map.getSource(heatmapSourceId)) {
        const source = map.getSource(heatmapSourceId) as mapboxgl.GeoJSONSource;
        source.setData(getWindHeatmapGeoJSON() as any);
      }
    } else {
      // Remove heatmap layer if it exists but is not needed
      if (map.getLayer(heatmapLayerId)) {
        map.removeLayer(heatmapLayerId);
      }
      if (map.getSource(heatmapSourceId)) {
        map.removeSource(heatmapSourceId);
      }
    }

    // Cleanup on unmount
    return () => {
      if (map.getLayer(vectorLayerId)) map.removeLayer(vectorLayerId);
      if (map.getSource(vectorSourceId)) map.removeSource(vectorSourceId);
      if (map.getLayer(heatmapLayerId)) map.removeLayer(heatmapLayerId);
      if (map.getSource(heatmapSourceId)) map.removeSource(heatmapSourceId);
    };
  }, [
    map,
    windPoints,
    vectorSourceId,
    vectorLayerId,
    heatmapSourceId,
    heatmapLayerId,
    vectorColor,
    vectorScale,
    showHeatmap,
    heatmapOpacity,
    heatmapRadius,
    selectedTime,
    timeWindow,
  ]);

  return null; // This component doesn't render anything on its own
};

export default WindLayer;