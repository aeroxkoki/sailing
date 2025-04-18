import React, { useEffect, useState } from 'react';
import mapboxgl from 'mapbox-gl';

interface TrackPoint {
  timestamp: number;
  longitude: number;
  latitude: number;
  speed?: number;
  heading?: number;
}

interface TrackLayerProps {
  map: mapboxgl.Map;
  trackPoints: TrackPoint[];
  trackColor?: string;
  trackWidth?: number;
  showMarkers?: boolean;
  fitBounds?: boolean;
  selectedPoint?: number;
  onPointClick?: (index: number) => void;
}

const TrackLayer: React.FC<TrackLayerProps> = ({
  map,
  trackPoints,
  trackColor = '#0080ff',
  trackWidth = 3,
  showMarkers = true,
  fitBounds = true,
  selectedPoint,
  onPointClick,
}) => {
  const [sourceId] = useState(`track-source-${Math.random().toString(36).substring(2, 9)}`);
  const [layerId] = useState(`track-layer-${Math.random().toString(36).substring(2, 9)}`);
  const [markersSourceId] = useState(`markers-source-${Math.random().toString(36).substring(2, 9)}`);
  const [markersLayerId] = useState(`markers-layer-${Math.random().toString(36).substring(2, 9)}`);
  const [selectedSourceId] = useState(`selected-source-${Math.random().toString(36).substring(2, 9)}`);
  const [selectedLayerId] = useState(`selected-layer-${Math.random().toString(36).substring(2, 9)}`);

  // Convert track points to GeoJSON
  const getTrackGeoJSON = () => {
    if (!trackPoints || trackPoints.length === 0) return null;

    return {
      type: 'Feature',
      properties: {},
      geometry: {
        type: 'LineString',
        coordinates: trackPoints.map(point => [point.longitude, point.latitude]),
      },
    };
  };

  // Convert track points to GeoJSON for markers
  const getMarkersGeoJSON = () => {
    if (!trackPoints || trackPoints.length === 0) return null;

    return {
      type: 'FeatureCollection',
      features: trackPoints.map((point, index) => ({
        type: 'Feature',
        properties: {
          id: index,
          timestamp: point.timestamp,
          speed: point.speed,
          heading: point.heading,
        },
        geometry: {
          type: 'Point',
          coordinates: [point.longitude, point.latitude],
        },
      })),
    };
  };

  // Get selected point as GeoJSON
  const getSelectedPointGeoJSON = () => {
    if (selectedPoint === undefined || !trackPoints || !trackPoints[selectedPoint]) return null;

    const point = trackPoints[selectedPoint];
    return {
      type: 'Feature',
      properties: {},
      geometry: {
        type: 'Point',
        coordinates: [point.longitude, point.latitude],
      },
    };
  };

  // Initialize and update sources and layers
  useEffect(() => {
    if (!map || !trackPoints || trackPoints.length === 0) return;

    // Add track source and layer if they don't exist
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
          'line-color': trackColor,
          'line-width': trackWidth,
        },
      });
    } else {
      // Update existing source
      const source = map.getSource(sourceId) as mapboxgl.GeoJSONSource;
      source.setData(getTrackGeoJSON() as any);
    }

    // Handle markers
    if (showMarkers) {
      if (!map.getSource(markersSourceId)) {
        map.addSource(markersSourceId, {
          type: 'geojson',
          data: getMarkersGeoJSON() as any,
        });

        map.addLayer({
          id: markersLayerId,
          type: 'circle',
          source: markersSourceId,
          paint: {
            'circle-radius': 4,
            'circle-color': trackColor,
            'circle-stroke-width': 1,
            'circle-stroke-color': '#ffffff',
          },
        });

        // Add click handler
        if (onPointClick) {
          map.on('click', markersLayerId, (e) => {
            if (e.features && e.features.length > 0) {
              const feature = e.features[0];
              const id = feature.properties?.id;
              if (id !== undefined) {
                onPointClick(id);
              }
            }
          });

          // Change cursor on hover
          map.on('mouseenter', markersLayerId, () => {
            map.getCanvas().style.cursor = 'pointer';
          });

          map.on('mouseleave', markersLayerId, () => {
            map.getCanvas().style.cursor = '';
          });
        }
      } else {
        // Update existing markers source
        const source = map.getSource(markersSourceId) as mapboxgl.GeoJSONSource;
        source.setData(getMarkersGeoJSON() as any);
      }
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
            'circle-radius': 8,
            'circle-color': '#ff0000',
            'circle-stroke-width': 2,
            'circle-stroke-color': '#ffffff',
          },
        });
      } else {
        // Update existing selected point source
        const source = map.getSource(selectedSourceId) as mapboxgl.GeoJSONSource;
        source.setData(getSelectedPointGeoJSON() as any);
      }
    }

    // Fit bounds if needed
    if (fitBounds && trackPoints.length > 1) {
      const bounds = new mapboxgl.LngLatBounds();
      trackPoints.forEach(point => {
        bounds.extend([point.longitude, point.latitude]);
      });

      map.fitBounds(bounds, {
        padding: 50,
        animate: true,
      });
    }

    // Cleanup on unmount
    return () => {
      if (map.getLayer(layerId)) map.removeLayer(layerId);
      if (map.getSource(sourceId)) map.removeSource(sourceId);
      if (map.getLayer(markersLayerId)) map.removeLayer(markersLayerId);
      if (map.getSource(markersSourceId)) map.removeSource(markersSourceId);
      if (map.getLayer(selectedLayerId)) map.removeLayer(selectedLayerId);
      if (map.getSource(selectedSourceId)) map.removeSource(selectedSourceId);
    };
  }, [
    map,
    trackPoints,
    sourceId,
    layerId,
    markersSourceId,
    markersLayerId,
    selectedSourceId,
    selectedLayerId,
    trackColor,
    trackWidth,
    showMarkers,
    fitBounds,
    selectedPoint,
    onPointClick,
  ]);

  return null; // This component doesn't render anything on its own
};

export default TrackLayer;