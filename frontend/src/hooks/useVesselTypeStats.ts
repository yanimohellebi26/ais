import { useState, useEffect } from "react";
import { useApi } from "./useApi";
import { toast } from "react-toastify";
import { AnalyticsFilters } from "../pages/Analytics/Components/interfaces";

export interface VesselTypeStat {
    vesselTypeId: number;
    vesselTypeDescription: string;
    vesselGroup: string;
    trajectoryCount: number;
    totalDistanceKm: number;
    averageSpeedKmh: number;
}

interface Props {
    filters?: AnalyticsFilters;
    topN?: number;
}

export const useVesselTypeStats = ({ filters, topN = 10 }: Props) => {
    const apiFetch = useApi();
    const [data, setData] = useState<VesselTypeStat[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const fetchData = async () => {
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

                const result = await apiFetch<VesselTypeStat[]>(
                    `/api/v1/statistics/vessel-type-statistics?topN=${topN}`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(body),
                });

                setData(result ?? []);
            } catch {
                toast.error("Failed to fetch vessel type statistics");
                setData([]);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [filters, topN]);

    return { data, loading };
};