import { useState, useEffect } from "react";
import { useApi } from "./useApi";
import { toast } from "react-toastify";
import { AnalyticsFilters } from "../pages/Analytics/Components/interfaces";

export type Granularity = "HOUR" | "DAY" | "WEEK" | "MONTH" | "AUTO";

export interface SeasonalityData {
    value: number | null;
    year: number | null;
    date: string | null;
    endDate: string | null;
    trajectoryCount: number;
    granularity: Granularity;
}

interface Props{
    filters?: AnalyticsFilters;
    granularity?: Granularity;
    year?: number | null;
}

export const useSeasonality = ({ filters, granularity = "AUTO", year }: Props) => {
    const apiFetch = useApi();
    const [data, setData] = useState<SeasonalityData[]>([]);
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

                const params = new URLSearchParams();
                params.set("granularity", granularity);
                if (year != null) params.set("year", String(year));

                const result = await apiFetch<SeasonalityData[]>(
                    `/api/v1/statistics/seasonality?${params.toString()}`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(body),
                    });

                setData(result ?? []);
            } catch {
                toast.error("Failed to fetch seasonality data");
                setData([]);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [filters, granularity, year]);

    return { data, loading };
};