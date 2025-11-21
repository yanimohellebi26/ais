import { useState, useEffect } from "react";
import { debounce } from "lodash";
import { useApi } from "./useApi";

interface Props {
    map:any;
    vesselId: number;
    date?: string;
    radiusKm?: number;
    enabled?: boolean;
}

export const useVesselPositionsRadius = ({ map, vesselId, date, radiusKm, enabled = true }: Props) => {
    const apiFetch = useApi();
    const [geoJson, setGeoJson] = useState<any | null>(null);

    useEffect(() => {
        if(!map || !enabled || vesselId==null) return;

        const fetchNearby = async () => {
            const params = new URLSearchParams();
            params.set("vesselId", vesselId.toString());
            if(date) params.set("date", date);
            if(radiusKm) params.set("radius_km", radiusKm.toString());

            const url = `/api/v1/positions/radius?${params.toString()}`;

            try {
                const data = await apiFetch<any>(url);
                setGeoJson(data);
            } catch {
                setGeoJson(null);
            }
        };

        const debouncedFetch = debounce(fetchNearby, 300);
        fetchNearby();

        map.on("moveend", debouncedFetch);

        return () => {
            map.off("moveend", debouncedFetch);
            debouncedFetch.cancel();
        };

    }, [map, apiFetch, vesselId, date, radiusKm, enabled]);
    return geoJson;
};