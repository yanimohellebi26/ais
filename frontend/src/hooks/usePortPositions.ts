import { useState, useEffect } from "react";
import { useApi } from "./useApi";

interface Props {
    map: any;
}

export const usePortPositions = ({ map}: Props) => {
    const apiFetch = useApi();
    const [geoJson, setGeoJson] = useState<any | null>(null);

    useEffect(() => {
        if (!map) return;

        const fetchPositions = async () => {
            const url = '/api/v1/ports';

            try {
                const data = await apiFetch<any>(url);
                setGeoJson(data);
            } catch {
                setGeoJson(null);
            }
        };
        fetchPositions();

    }, [map, apiFetch]);

    return geoJson;
};
