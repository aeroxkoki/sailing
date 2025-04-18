import React, { useRef, useEffect, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

interface MapViewProps {
  initialCenter?: [number, number]; // [longitude, latitude]
  initialZoom?: number;
  style?: string;
  width?: string;
  height?: string;
  className?: string;
  onMapLoad?: (map: mapboxgl.Map) => void;
  children?: React.ReactNode;
}

const MapView: React.FC<MapViewProps> = ({
  initialCenter = [139.767, 35.681], // Tokyo by default
  initialZoom = 10,
  style = 'mapbox://styles/mapbox/outdoors-v12',
  width = '100%',
  height = '400px',
  className = '',
  onMapLoad,
  children,
}) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);

  // Load environment variables or use defaults
  const mapboxToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN || '';

  useEffect(() => {
    if (!mapContainer.current) return;

    // Set access token
    mapboxgl.accessToken = mapboxToken;

    // Initialize map
    const mapInstance = new mapboxgl.Map({
      container: mapContainer.current,
      style: style,
      center: initialCenter,
      zoom: initialZoom,
    });

    // Add navigation controls
    mapInstance.addControl(new mapboxgl.NavigationControl(), 'top-right');

    // Add scale control
    mapInstance.addControl(
      new mapboxgl.ScaleControl({ maxWidth: 80, unit: 'metric' }),
      'bottom-left'
    );

    // Setup event handlers
    mapInstance.on('load', () => {
      setMapLoaded(true);
      if (onMapLoad) onMapLoad(mapInstance);
    });

    // Cleanup on unmount
    map.current = mapInstance;
    return () => {
      mapInstance.remove();
      map.current = null;
    };
  }, [initialCenter, initialZoom, style, onMapLoad, mapboxToken]);

  // Expose map context to children if needed
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