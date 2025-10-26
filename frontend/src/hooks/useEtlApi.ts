import {useEtlAuth} from "../context/EtlAuthContext";

const ETL_API_BASE_URL = import.meta.env.VITE_ETL_API_URL?.replace(/\/$/, "");
if (!ETL_API_BASE_URL) throw new Error("Missing VITE_ETL_API_URL env variable");

type ApiOptions = Omit<RequestInit, "body"> & { body?: any };

export function useEtlApi() {
    const { apiKey } = useEtlAuth();

    return async <T = any>(endpoint: string, options: ApiOptions = {}): Promise<T> => {
        const url = `${ETL_API_BASE_URL}${endpoint}`;
        const headers = new Headers(options.headers);

        if (apiKey) headers.set("x-api-key", apiKey);
        headers.set("Content-Type", "application/json");

        const response = await fetch(url, {
            ...options,
            headers,
            body: options.body ? JSON.stringify(options.body) : undefined,
        });

        const contentType = response.headers.get("Content-Type");
        const data = contentType?.includes("application/json")
            ? await response.json()
            : await response.text();

        if (!response.ok) {
            throw {
                name: "EtlApiError",
                message: data?.message || `ETL API error: ${response.status}`,
                statusCode: data?.statusCode ?? response.status,
                path: endpoint,
                timestamp: new Date().toISOString(),
            };
        }

        return data as T;
    };
}
