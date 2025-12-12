import React, { useRef, useEffect, useState } from "react";
import { Map, Source, Layer } from "@vis.gl/react-maplibre";
import "maplibre-gl/dist/maplibre-gl.css";
import { useNavigate } from "react-router-dom";
import { useApi } from "../../../hooks/useApi";
import { MAP_STYLES, WIDGET_VIEW_STATE, VESSEL_COLORS, PORT_COLORS } from "../constants/mapStyles";

interface props {
    lat?: number;
    lon?: number;
}

const PortWidget: React.FC<props> = ({ lat, lon }) => {
    const navigate = useNavigate();
    const mapRef = useRef<any>(null)
    const api = useApi();
    const [geoJson, setGeoJson] = useState<any | null>(null);

    useEffect(() => {
        if (lat === undefined || lon === undefined) {
            setGeoJson(null)
            return;
        }

        const fetchNearestPort = async () => {
            try {
                const data = await api(`/api/v1/ports/nearest?lat=${lat}&lon=${lon}`);
                setGeoJson(data);
            } catch (err: any) {
                console.log(err)
                setGeoJson(null);
            }
        };

        fetchNearestPort();
    }, [lat, lon, api]);

    useEffect(() => {
        if (!mapRef.current ||!geoJson?.features?.[0]) return;

        const coords = geoJson.features[0].geometry?.coordinates;

        if (!Array.isArray(coords) || coords.length < 2) return;

        const [longitude, latitude] = coords;
        mapRef.current.flyTo({center: [longitude, latitude], zoom: 8});
    }, [geoJson]);

    const hasPort = !!geoJson?.features?.length;

    return (
        <div 
            className="relative w-full h-full rounded-x1 overflow-hidden cursor-pointer"
            onClick={() => navigate("/dashboard/map")}
        >
            <Map
                ref={mapRef}
                initialViewState={WIDGET_VIEW_STATE}
                style={{width: "100%", height: "100%"}}
                mapStyle={MAP_STYLES.STANDARD}
            >
                {hasPort && (
                    <Source id="port-source" type="geojson" data={geoJson}>
                        <Layer
                            id="port-point"
                            type="circle"
                            paint={{
                                "circle-radius": 7,
                                "circle-color": PORT_COLORS.NORMAL,
                                "circle-stroke-width": 2,
                                "circle-stroke-color": "#FFFFFF"
                            }}
                        />
                    </Source>
                )}
            </Map>

            {!hasPort && (
                <div className="absolute inset-0 flex items-center justify-center text-2xl bg-black/20 font-semibold text-black text-center p-4 rounded-xl">
                    <span>No port found near this vessel.</span>
                </div>
            )}

        </div>
    );
};

export default PortWidget;