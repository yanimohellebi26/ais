import React, { use, useEffect, useState } from "react";
import { Source, Layer } from "@vis.gl/react-maplibre";
import { useApi } from "../../hooks/useApi";

interface VesselLayerProps {
    endpoint?: string;
    mmsis?: string[];
}

const VesselLayer : React.FC<VesselLayerProps> = ({
    endpoint = "/api/v1/positions/latest?page=0&size=10000",
    mmsis,
}) => {
    const apiFetch = useApi();
    const [geoJson, setGeoJson] = useState<any | null>(null);

    useEffect(() => {
        const fetchPositions = async () => {
            try {
                const query =
                    mmsis && mmsis.length > 0
                        ? endpoint.includes("?")
                            ? `${endpoint}&mmsis=${mmsis.join(",")}`
                            : `${endpoint}?mmsis=${mmsis.join(",")}`
                        : endpoint;

                const data = await apiFetch<any>(query);
                setGeoJson(data)
            } catch (err: any) {
                if (err.statusCode === 204) {
                    console.log("No positions");
                    setGeoJson(null);
                } else {
                    console.error("Error while loading positions ", err);
                }
            }
        }

        fetchPositions();
    }, [apiFetch, endpoint, mmsis]);

    if (!geoJson) return null;

    return (
        <Source id="vessels-source" type="geojson" data={geoJson}>
            <Layer 
                id="vessels-layer"
                type="circle"
                paint={{
                    "circle-radius" : 6,
                    "circle-color" : "#007BFF",
                    "circle-stroke-width" : 2,
                    "circle-stroke-color" : "#FFFFFF"
                }}
            />
        </Source>
    )
}

export default VesselLayer