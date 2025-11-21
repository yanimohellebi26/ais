import { useCallback, useState } from "react";
import { toast } from "react-toastify";
import { useApi } from "../../../hooks/useApi";
import { PageResponse, RequestPropertyAdmin } from "../../../types";

export type RequestPropertyRow = {
    id: number;
    userId: number;
    username: string;
    userEmail: string;
    userRole: string;
    mmsi: string;
    fileId: number;
    fileName: string;
    createdAt: string;
};

const mapToRow = (item: RequestPropertyAdmin): RequestPropertyRow => ({
    id: item.id,
    userId: item.userId,
    username: item.username,
    userEmail: item.userEmail,
    userRole: item.userRole,
    mmsi: item.mmsi,
    fileId: item.fileId,
    fileName: item.fileName || `file-${item.fileId}`,
    createdAt: item.createdAt,
});

export const useRequestProperty = (setLoading: (value: boolean) => void) => {
    const api = useApi();
    const [requests, setRequests] = useState<RequestPropertyRow[]>([]);

    const fetchRequests = useCallback(async () => {
        setLoading(true);
        try {
            const page = await api<PageResponse<RequestPropertyAdmin>>("/api/v1/request-property");
            setRequests(page.content.map(mapToRow));
        } catch {
            toast.error("Failed to load request properties");
        } finally {
            setLoading(false);
        }
    }, [api]);

    const removeFromState = useCallback((id: number) => {
        setRequests(prev => prev.filter(item => item.id !== id));
    }, []);

    return { requests, fetchRequests, removeFromState };
};
