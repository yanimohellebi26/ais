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
            try {
                const targetVesselData = await apiFetch<any>(`/api/v1/positions/${vesselId}`);

                if(!radiusKm){
                    setGeoJson(targetVesselData);
                    return;
                }
                const params = new URLSearchParams();
                params.set("vesselId", vesselId.toString());
                if(date) params.set("date", date);
                if(radiusKm) params.set("radiusKm", radiusKm.toString());

                const url = `/api/v1/positions/radius?${params.toString()}`;
                const data = await apiFetch<any>(url);

                const feature = [
                    ...targetVesselData.features,
                    ...(data?.features?.filter((f: any) => f.properties.vesselId !== vesselId) || [])
                ];

                setGeoJson({
                    type: "FeatureCollection",
                    features: feature
                });
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