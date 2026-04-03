import { useState, useEffect } from "react";
import { useApi } from "./useApi";
import { toast } from "react-toastify";
import { AnalyticsFilters } from "../pages/Analytics/Components/interfaces";

export interface CountryPresenceResult {
    countryName: string;
    alpha2: string;
    vesselCount: number;
}

interface Props {
    filters?: AnalyticsFilters;
    topN?: number;
}

export const useCountryPresence = ({ filters, topN = 10 }: Props) => {
    const apiFetch = useApi();
    const [data, setData] = useState<CountryPresenceResult[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            try {
                const body = {
                    startDate:   filters?.dateFrom    ?? null,
                    endDate:     filters?.dateTo      ?? null,
                    vesselType:  filters?.vesselType  ?? null,
                    vesselGroup: filters?.vesselGroup ?? null,
                    country:     filters?.country     ?? null,
                    latitude:    filters?.latitude    ?? null,
                    longitude:   filters?.longitude   ?? null,
                    radius:      filters?.radius      ?? null,
                };

                const result = await apiFetch<CountryPresenceResult[]>(
                    `/api/v1/analytics/country-presence?topN=${topN}`,
                    {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(body),
                    }
                );
                setData(result ?? []);
            } catch {
                toast.error("Failed to fetch country presence data.");
                setData([]);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [filters, topN]);

    return { data, loading };
};