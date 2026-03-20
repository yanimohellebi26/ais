import { useCallback, useEffect, useState } from "react";
import { MapLibreEvent } from "maplibre-gl";
import { useApi } from "../../../hooks/useApi";


export const useProtectedArea = (map: any) => {
    const [geoJson, setGeoJson] = useState<any>(null);
    const api = useApi();

    const fetchProtectedArea = useCallback(async () => {
        if (!map) return;

        const bounds = map.getBounds();
        const url = `/api/v1/protected-area?minLong=${bounds.getWest()}&minLat=${bounds.getSouth()}&maxLong=${bounds.getEast()}&maxLat=${bounds.getNorth()}`;
        
        try {
            const data = await api(url, {
                method: "GET",
                responseType: "json"
            });
            setGeoJson(data);
        } catch (error) {
            console.error("Error fetching protected area data:", error);
        }
    
    }, [map, api]);

    useEffect(() => {
        if (!map) return;
        fetchProtectedArea();
        map.on("moveend", fetchProtectedArea);
        return () => {
                map.off("moveend", fetchProtectedArea);
            }
    }, [map, fetchProtectedArea]);
    
    return geoJson;
};