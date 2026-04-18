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
}

export const usePortRoutes = ({ filters }: Props) => {
    const apiFetch = useApi();
    const [data, setData] = useState<PortRoutesData | null>(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const fetchPortRoutes = async () => {
            setLoading(true);
            try {
                const body = {
                    startDate: filters?.dateFrom ?? null,
                    endDate: filters?.dateTo ?? null,
                    vesselType: filters?.vesselType ?? null,
                    vesselGroup: filters?.vesselGroup ?? null,
                    country: filters?.country ?? null,
                    latitude: filters?.latitude ?? null,
                    longitude: filters?.longitude ?? null,
                    radius: filters?.radius ?? null,
                };

                const result = await apiFetch<PortRoutesData>(
                    `/api/v1/trajectories/port-routes`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(body),
                    }
                );

                setData(result ?? { type: "FeatureCollection", features: [] });
            } catch (error) {
                toast.error("Failed to fetch port routes data");
                setData({ type: "FeatureCollection", features: [] });
            } finally {
                setLoading(false);
            }
        };

        fetchPortRoutes();
    }, [filters, apiFetch]);

    return { data, loading };
};