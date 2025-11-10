import React, { useEffect, useState } from "react";
import { Source, Layer, useMap } from "@vis.gl/react-maplibre";
import { useApi } from "../../hooks/useApi";
import { debounce } from "lodash";
import {toast} from "react-toastify";

interface VesselLayerProps {
    limit?: number
}

const VesselLayer : React.FC<VesselLayerProps> = ({
    limit = 200
}) => {
    const apiFetch = useApi();
    const [geoJson, setGeoJson] = useState<any | null>(null);
    const { current: map } = useMap();

    useEffect(() => {

        if (!map) return;

        const fetchPositionsInBounds = async () => {
            const bounds = map.getBounds();
            if (!bounds) return;

            const minLat = bounds.getSouth();
            const maxLat = bounds.getNorth();
            const minLon = bounds.getWest();
            const maxLon = bounds.getEast();

            const zoom = map.getZoom();
            const dynamicLimit = zoom < 5 ? limit : zoom < 8 ? limit * 3 : limit * 5;

            const query = `/api/v1/positions/latest/in-bounds?minLat=${minLat}&maxLat=${maxLat}&minLon=${Math.max(-180, Math.min(minLon, 180))}&maxLon=${Math.max(-180, Math.min(maxLon, 180))}&limit=${dynamicLimit}`;

            try {
                const data = await apiFetch<any>(query);
                setGeoJson(data);
            } catch (err: any) {
                if (err.statusCode === 204) {
                    setGeoJson(null);
                } else {
                    toast.error("Error loading vessel positions");
                }
            }
        }

        const debouncedFetch = debounce(fetchPositionsInBounds, 500, { leading: true, trailing: false });

        fetchPositionsInBounds();

        map.on("moveend", debouncedFetch);

        return () => {
            map.off("moveend", debouncedFetch);
            debouncedFetch.cancel();
        }
    }, [map, apiFetch, limit]);

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