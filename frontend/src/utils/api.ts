import { useAuth } from "../context/AuthContext";

const API_BASE_URL = import.meta.env.VITE_API_URL?.replace(/\/$/, "");
if (!API_BASE_URL) throw new Error("Missing VITE_API_URL env variable");

type ApiOptions = Omit<RequestInit, "body"> & { body?: any };

export function useApi() {
    const { user } = useAuth();

    const apiFetch = async <T = any>(endpoint: string, options: ApiOptions = {}): Promise<T> => {
        const url = `${API_BASE_URL}${endpoint}`;
        const headers = new Headers(options.headers);
        if (user?.token) headers.set("Authorization", `Bearer ${user.token}`);

        const response = await fetch(url, { ...options, headers });
        const contentType = response.headers.get("Content-Type");

        let data: any;
        if (contentType?.includes("application/json")) data = await response.json();
        else data = await response.text();

        if (!response.ok) throw new Error((data && data.message) || `API error: ${response.status}`);

        return data as T;
    };

    return apiFetch;
}

