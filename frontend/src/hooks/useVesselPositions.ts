import { useState, useEffect } from "react";
import { debounce } from "lodash";
import { useApi } from "./useApi";
import { DateRange } from "react-day-picker";
import { format } from "date-fns";

interface Props {
    map: any;
    limit?: number;
    dateRange?: DateRange;
}

export const useVesselPositions = ({ map, limit = 200, dateRange }: Props) => {
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
                const dist = Math.hypot(center[0] - lastCenter[0], center[1] - lastCenter[1]);
                if (dist < 0.1) return; // If not moved enough
            }
            lastCenter = center;

            const zoom = map.getZoom();
            const dynamicLimit = zoom < 5 ? limit : zoom < 8 ? limit * 3 : limit * 5;

            // Common bounds params
            const minLat = bounds.getSouth();
            const maxLat = bounds.getNorth();
            const minLon = Math.max(-179.9999, Math.min(bounds.getWest(), 179.9999));
            const maxLon = Math.max(-179.9999, Math.min(bounds.getEast(), 179.9999));

            let url: string;
            const params = new URLSearchParams();

            if (dateRange?.from && dateRange?.to) {
                // Date range API
                params.set("dateStart", format(dateRange.from, "yyyy-MM-dd"));
                params.set("dateEnd", format(dateRange.to, "yyyy-MM-dd"));
                params.set("minLat", minLat.toString());
                params.set("maxLat", maxLat.toString());
                params.set("minLon", minLon.toString());
                params.set("maxLon", maxLon.toString());
                params.set("limit",dynamicLimit.toString());

                url = `/api/v1/positions?${params.toString()}`;
            } else {
                // Latest positions API
                params.set("minLat", minLat.toString());
                params.set("maxLat", maxLat.toString());
                params.set("minLon", minLon.toString());
                params.set("maxLon", maxLon.toString());
                params.set("limit", dynamicLimit.toString());

                url = `/api/v1/positions/latest/in-bounds?${params.toString()}`;
            }

            try {
                const data = await apiFetch<any>(url);
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
    }, [map, apiFetch, limit, dateRange]);

    return geoJson;
};
