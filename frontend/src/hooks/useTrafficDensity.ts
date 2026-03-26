import { useState, useEffect } from "react";
import { debounce } from "lodash";
import { useApi } from "./useApi";
import { DateRange } from "react-day-picker";
import { format } from "date-fns";
import { toast } from "react-toastify";

interface Props {
    map: any;
    gridSize?: number;
    dateRange?: DateRange;
}

export const useTrafficDensity = ({map, gridSize = 0.1, dateRange}: Props) => {
    const apiFetch = useApi();
    const [geoJson, setGeoJson] = useState<any | null>(null);

    useEffect(() => {
        if (!map) return;

        let lastCenter: [number, number] | null = null;

        const fetchDensity = async () => {
            const bounds = map.getBounds();
            if (!bounds) return;

            const center: [number, number] = [map.getCenter().lng, map.getCenter().lat];
            if (lastCenter) {
                const dist = Math.hypot(center[0] - lastCenter[0], center[1] - lastCenter[1]);
                if (dist < 0.1) return; // If not moved enough
            }
            lastCenter = center;

            const minLat = bounds.getSouth();
            const maxLat = bounds.getNorth();
            const minLon = Math.max(-179.9999, Math.min(bounds.getWest(), 179.9999));
            const maxLon = Math.max(-179.9999, Math.min(bounds.getEast(), 179.9999));

            const params = new URLSearchParams();
            params.set("minLat", minLat.toString());
            params.set("maxLat", maxLat.toString());
            params.set("minLon", minLon.toString());
            params.set("maxLon", maxLon.toString());
            params.set("gridSize", gridSize.toString());

            if (dateRange?.from && dateRange?.to) {
                params.set("dateStart", format(dateRange.from, "yyyy-MM-dd"));
                params.set("dateEnd", format(dateRange.to, "yyyy-MM-dd"));
            }

            const url = `/api/v1/analytics/traffic-density?${params.toString()}`;

            try {
                const data = await apiFetch<any>(url);
                if(!data || (data.features && data.features.length === 0)){
                    toast.error("No data available");
                    setGeoJson(null);
                    return;
                }
                setGeoJson(data);
            } catch (err){
                toast.error("Failed to fetch positions.");
                setGeoJson(null);
            }
        };

        const debouncedFetch = debounce(fetchDensity, 500);
        fetchDensity();

        map.on("moveend", debouncedFetch);
        map.on("zoomend", debouncedFetch);

        return () => {
            map.off("moveend", debouncedFetch);
            map.off("zoomend", debouncedFetch);
            debouncedFetch.cancel();
        };
    },[map, apiFetch, gridSize, dateRange]);

    return geoJson;
};