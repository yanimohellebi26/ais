import React, { useEffect, useRef } from "react";
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

const MapComponent: React.FC = () => {
  

  useEffect(() => {
    if (!mapContainer.current) return;

    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: "https://demotiles.maplibre.org/style.json",
      center: [2.3522, 48.8566],
      zoom: 5,
    });

    map.addControl(new maplibregl.NavigationControl(), "top-right");
    new maplibregl.Marker().setLngLat([2.3522, 48.8566]).addTo(map);

    return () => map.remove();
  }, []);

  return (
    <div
      ref={mapContainer}
      style={{ width: "100%", height: "100vh" }}
    />
  );
};

export default MapComponent;
const mapContainer = useRef<HTMLDivElement | null>(null);