import { useEtlAuth } from "../context/EtlAuthContext";
import { etlApiEmitter } from "./useEtlApiEmitter";

const ETL_API_BASE_URL = import.meta.env.VITE_ETL_API_URL?.replace(/\/$/, "");
if (!ETL_API_BASE_URL) throw new Error("Missing VITE_ETL_API_URL env variable");

type ApiOptions = Omit<RequestInit, "body"> & {
    body?: any;
    responseType?: "json" | "text" | "blob";
};

export function useEtlApi() {
    const { apiKey } = useEtlAuth();

    return async <T = any>(endpoint: string, options: ApiOptions = {}): Promise<T> => {
        const url = `${ETL_API_BASE_URL}${endpoint}`;
        const headers = new Headers(options.headers);

        if (apiKey) headers.set("x-api-key", apiKey);

        if (!(options.body instanceof FormData)) {
            headers.set("Content-Type", "application/json");
        }

        const response = await fetch(url, {
            ...options,
            headers,
            body: options.body instanceof FormData ? options.body : options.body ?? undefined,
        });

        const contentType = response.headers.get("Content-Type") || "";

        let data: any;
        if (options.responseType === "blob") {
            data = await response.blob();
        } else if (options.responseType === "text" || contentType.includes("text/")) {
            data = await response.text();
        } else if (options.responseType === "json" || contentType.includes("application/json")) {
            data = await response.json();
        } else {
            data = await response.text();
        }

        if (!response.ok) {
            throw {
                name: "EtlApiError",
                message: data?.detail || data?.message || `ETL API error: ${response.status}`,
                statusCode: data?.statusCode ?? response.status,
                path: endpoint,
                timestamp: new Date().toISOString(),
            };
        }

        // If mutating request, emit
        if (["POST", "PUT", "DELETE"].includes(options.method?.toUpperCase() || "")) {
            etlApiEmitter.emit();
        }

        return data as T;
    };
}