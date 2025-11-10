import { useState, useEffect } from "react";
import { debounce } from "lodash";
import {useApi} from "./useApi";

interface Props {
    map: any;
    limit?: number;
}

export const useVesselPositions = ({ map, limit = 200 }: Props) => {
    const apiFetch = useApi();
    const [geoJson, setGeoJson] = useState<any | null>(null);

    useEffect(() => {
        if (!map) return;

        let lastCenter: [number, number] | null = null;

        const fetchPositions = async () => {
            const bounds = map.getBounds();
            if (!bounds) return;

            const center: [number, number] = [map.getCenter().lng, map.getCenter().lat];
            if (lastCenter) {
                const dist = Math.sqrt(
                    Math.pow(center[0] - lastCenter[0], 2) +
                    Math.pow(center[1] - lastCenter[1], 2)
                );
                if (dist < 0.1) return; //If not moved enough
            }
            lastCenter = center;

            const zoom = map.getZoom();
            const dynamicLimit = zoom < 5 ? limit : zoom < 8 ? limit * 3 : limit * 5;

            let query = `/api/v1/positions/latest/in-bounds?minLat=${bounds.getSouth()}&maxLat=${bounds.getNorth()}&minLon=${Math.max(-179.9999, Math.min(bounds.getWest(), 179.9999))}&maxLon=${Math.max(-179.9999, Math.min(bounds.getEast(), 179.9999))}&limit=${dynamicLimit}`;

            try {
                const data = await apiFetch<any>(query);
                setGeoJson(data);
            } catch {
                setGeoJson(null);
            }
        };

        const debouncedFetch = debounce(fetchPositions, 500);
        fetchPositions();

        map.on("moveend", debouncedFetch);

        return () => {
            map.off("moveend", debouncedFetch);
            debouncedFetch.cancel();
        };
    }, [map, apiFetch, limit]);

    return geoJson;
};
