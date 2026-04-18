import { useState, useEffect } from "react";
import { useApi } from "./useApi";
import { toast } from "react-toastify";
import { AnalyticsFilters } from "../pages/Analytics/Components/interfaces";

export interface PortRoutesData {
    type: "FeatureCollection";
    features: {
        type: "Feature";
        geometry: {
            type: "LineString";
            coordinates: number[][];
        };
        properties: {
            srcPort: string;
            destPort: string;
            count: number;
            avgDuration: number;
        };
    }[];
}

interface Props {
    filters?: AnalyticsFilters;
    minLat?: number;
    maxLat?: number;
    minLon?: number;
    maxLon?: number;
    zoom?: number;
}

export const usePortRoutes = ({ filters, map }: { filters?: AnalyticsFilters, map: any }) => {
    const apiFetch = useApi();
    const [data, setData] = useState<PortRoutesData | null>(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const fetchPortRoutes = async () => {
            if (!map || !map.getMap) return;
            const nativeMap = map.getMap();
            
            setLoading(true);
            try {
                const bounds = nativeMap.getBounds();
                const zoom = Math.floor(nativeMap.getZoom());

                const params = new URLSearchParams({
                    minLat: bounds.getSouth().toString(),
                    maxLat: bounds.getNorth().toString(),
                    minLon: bounds.getWest().toString(),
                    maxLon: bounds.getEast().toString(),
                    zoom: zoom.toString(),
                    startDate: filters?.dateFrom ?? "",
                    endDate: filters?.dateTo ?? "",
                    vesselType: filters?.vesselType?.toString() ?? "",
                    vesselGroup: filters?.vesselGroup?.toString() ?? "",
                    country: filters?.country?.toString() ?? "",
                    latitude: filters?.latitude?.toString() ?? "",
                    longitude: filters?.longitude?.toString() ?? "",
                    radius: filters?.radius?.toString() ?? "",
                });

                const cleanParams = new URLSearchParams();
                params.forEach((value, key) => {
                    if (value !== "" && value !== "null") cleanParams.append(key, value);
                });

                const result = await apiFetch<PortRoutesData>(
                    `/api/v1/trajectories/port-routes?${cleanParams.toString()}`, 
                    { method: "GET" }
                );

                setData(result ?? { type: "FeatureCollection", features: [] });
            } catch (error) {
                toast.error("Failed to fetch port routes data");
                setData({ type: "FeatureCollection", features: [] });
            } finally {
                setLoading(false);
            }
        };

        const nativeMap = map?.getMap?.();
        if (nativeMap) {
            fetchPortRoutes();
            nativeMap.on("moveend", fetchPortRoutes);
            nativeMap.on("zoomend", fetchPortRoutes);
            return () => {
                nativeMap.off("moveend", fetchPortRoutes);
                nativeMap.off("zoomend", fetchPortRoutes);
            };
        }
    }, [filters, map, apiFetch]);

    return { data, loading };
};