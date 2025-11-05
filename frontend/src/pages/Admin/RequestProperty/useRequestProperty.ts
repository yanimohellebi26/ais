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
    userId: item.userid,
    username: item.username,
    userEmail: item.user_email,
    userRole: item.user_role,
    mmsi: item.mmsi,
    fileId: item.fileid,
    fileName: item.file_name || `file-${item.fileid}`,
    createdAt: item.created_at,
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
