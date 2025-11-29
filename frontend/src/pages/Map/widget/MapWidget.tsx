import React, { useRef, useEffect, useState } from "react";
import { Map, Source, Layer } from "@vis.gl/react-maplibre";
import "maplibre-gl/dist/maplibre-gl.css";
import { useNavigate } from "react-router-dom";
import { useApi } from "../../../hooks/useApi";

interface Props {
    vesselId: number;
}

const MapWidget: React.FC<Props> = ({ vesselId }) => {
    const navigate = useNavigate();
    const mapRef = useRef<any>(null);
    const api = useApi();
    const [geoJson, setGeoJson] = useState<any>(null);

    useEffect(() => {
        const fetchPosition = async () => {
            try {
                const data = await api(`/api/v1/positions/latest?ids=${vesselId}`);
                setGeoJson(data);
            } catch (err: any) {
                console.error(err);
            }
        };
        fetchPosition();
    }, [vesselId, api]);

    useEffect(() => {
        if (!mapRef.current || !geoJson?.features?.[0]) return;
        const [lng, lat] = geoJson.features[0].geometry.coordinates;
        mapRef.current.flyTo({ center: [lng, lat], zoom: 4 });
    }, [geoJson]);

    const hasPositions = geoJson?.features?.length > 0;

    return (
        <div
            className="relative w-full h-full rounded-xl overflow-hidden cursor-pointer"
            onClick={() => navigate("/dashboard/map")}
        >
            <Map
                ref={mapRef}
                initialViewState={{
                    longitude: 0,
                    latitude: 0,
                    zoom: 1,
                }}
                style={{ width: "100%", height: "100%" }}
                mapStyle="https://demotiles.maplibre.org/style.json"
            >
                {hasPositions && (
                    <Source id="vessel-source" type="geojson" data={geoJson}>
                        <Layer
                            id="vessel-point"
                            type="circle"
                            paint={{
                                "circle-radius": 6,
                                "circle-color": "#007BFF",
                                "circle-stroke-width": 2,
                                "circle-stroke-color": "#FFFFFF",
                            }}
                        />
                    </Source>
                )}
            </Map>

            {!hasPositions && (
                <div className="absolute inset-0 flex items-center justify-center text-2xl bg-black/20 font-semibold text-black text-center p-4 rounded-xl">
                    <span>No position data available for this vessel.</span>
                </div>
            )}
        </div>
    );
};

export default MapWidget;
