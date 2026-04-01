import { useState, useEffect } from "react";
import { debounce } from "lodash";
import { useApi } from "./useApi";
import { toast } from "react-toastify";
import { AnalyticsFilters } from "../pages/Analytics/Components/interfaces";

interface Props {
    map: any;
    gridSize?: number;
    filters?: AnalyticsFilters;
}

export const useTrafficDensity = ({ map, gridSize = 0.1, filters }: Props) => {
    const apiFetch = useApi();
    const [geoJson, setGeoJson] = useState<any | null>(null);
    const [stats, setStats] = useState<{ min: number; max: number } | null>(null);

    useEffect(() => {
        if (!map) return;

        let lastCenter: [number, number] | null = null;

        const getPercentile = (arr: number[], p: number) => {
            const index = Math.floor((p / 100) * arr.length);
            return arr[index];
        };

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

            if (filters) {
                if (filters.dateFrom) params.set("startDate", filters.dateFrom);
                if (filters.dateTo) params.set("endDate", filters.dateTo);
                if (filters.vesselType) params.set("vesselType", filters.vesselType.toString());
                if (filters.vesselGroup) params.set("vesselGroup", filters.vesselGroup);
                if (filters.country) params.set("country", filters.country);
            }

            const url = `/api/v1/analytics/traffic-density?${params.toString()}`;

            try {
                const data = await apiFetch<any>(url);
                if(!data || (data.features && data.features.length === 0)){
                    toast.error("No data available for heatmap");
                    setGeoJson(null);
                    return;
                }
                const densities = data.features
                    .map((f: any) => f.properties.density)
                    .sort((a: number, b: number) => a - b);

                const min = getPercentile(densities, 5);
                const max = getPercentile(densities, 95);

                setStats({
                    min,
                    max: Math.max(min + 1, max)
                });

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
    },[map, apiFetch, gridSize, filters]);

    return { geoJson, stats };
};