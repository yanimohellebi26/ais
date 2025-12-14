import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useLoading } from "../../../context/LoadingContext";
import { useApi } from "../../../hooks/useApi";
import { toast } from "react-toastify";
import { ColumnDef } from "@tanstack/react-table";
import { RequestUserCell } from "./RequestUserCell";
import { RequestFileCell } from "./RequestFileCell";
import { RequestActionsCell } from "./RequestActionsCell";
import {RequestPropertyRow, useRequestProperty} from "./useRequestProperty";
import Breadcrumbs from "../../../components/BaseComponents/Breadcrumbs";
import {GenericTable} from "../../../components/BaseComponents/GenericTable";
import Swal from "sweetalert2";


const confirmAction = async (title: string, text: string, icon: "question" | "warning" = "question") =>
    await Swal.fire({ title, text, icon, showCancelButton: true, confirmButtonText: "Confirm", cancelButtonText: "Cancel" });

const AdminRequestProperty: React.FC = () => {
    const { setLoading } = useLoading();
    const api = useApi();

    const { requests, fetchRequests, removeFromState } = useRequestProperty(setLoading);

    const [loadingRow, setLoadingRow] = useState<{ id: number; type: "download" | "preview" | "action" } | null>(null);

    useEffect(() => {
        fetchRequests();
    }, [fetchRequests]);

    const fetchFileBlob = useCallback(async (fileId: number): Promise<Blob> => {
        const response = await api(`/api/v1/uploads/${fileId}/download`, { responseType: "blob" });
        return new Blob([response as Blob], { type: "application/pdf" });
    }, [api]);

    const handleDownload = useCallback(async (row: RequestPropertyRow) => {
        setLoadingRow({ id: row.id, type: "download" });
        try {
            const blob = await fetchFileBlob(row.fileId);
            const link = document.createElement("a");
            link.href = URL.createObjectURL(blob);
            link.download = row.fileName;
            link.click();
            toast.success(`File ${row.fileName} downloaded`);
        } catch {
            toast.error("Unable to download file");
        } finally {
            setLoadingRow(null);
        }
    }, [fetchFileBlob]);

    const handlePreview = useCallback(async (row: RequestPropertyRow) => {
        setLoadingRow({ id: row.id, type: "preview" });
        try {
            const blob = await fetchFileBlob(row.fileId);
            const url = URL.createObjectURL(blob);
            window.open(url, "_blank");
            setTimeout(() => URL.revokeObjectURL(url), 60000);
        } catch {
            toast.error("Failed to open file");
        } finally {
            setLoadingRow(null);
        }
    }, [fetchFileBlob]);

    const handleAccept = useCallback(async (row: RequestPropertyRow) => {
        const confirm = await confirmAction(`Accept ownership for ${row.username}?`, "The user will become owner of the vessel");
        if (!confirm.isConfirmed) return;

        setLoadingRow({ id: row.id, type: "action" });
        try {
            await api("/api/v1/vessels/related", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ userId: row.userId, vesselId: row.vesselId }),
            });
            await api(`/api/v1/request-property/${row.id}`, { method: "DELETE" });
            toast.success("Request accepted");
            removeFromState(row.id);
        } catch {
            toast.error("Failed to accept the request");
        } finally {
            setLoadingRow(null);
        }
    }, [api, removeFromState]);

    const handleRefuse = useCallback(async (row: RequestPropertyRow) => {
        const confirm = await confirmAction(
            `Refuse ownership for ${row.username}?`,
            "The associated file will be deleted",
            "warning"
        );
        if (!confirm.isConfirmed) return;

        setLoadingRow({ id: row.id, type: "action" });
        try {
            await api(`/api/v1/request-property/${row.id}`, { method: "DELETE" });
            toast.success("Request refused");
            removeFromState(row.id);
        } catch {
            toast.error("Failed to refuse the request");
        } finally {
            setLoadingRow(null);
        }
    }, [api, removeFromState]);

    const columns = useMemo<ColumnDef<RequestPropertyRow>[]>(() => [
        {
            id: "user",
            header: "User",
            cell: ({ row }) => <RequestUserCell row={row.original} />,
        },
        { accessorKey: "mmsi", header: "MMSI" },
        {
            id: "createdAt",
            header: "Date",
            cell: ({ row }) => new Date(row.original.createdAt).toLocaleString(),
        },
        {
            id: "file",
            header: "File",
            cell: ({ row }) => (
                <RequestFileCell
                    row={row.original}
                    onDownload={handleDownload}
                    onPreview={handlePreview}
                    isLoading={
                        loadingRow?.id === row.original.id && loadingRow.type !== "action"
                            ? loadingRow.type
                            : null
                    }
                />
            ),
        },
        {
            id: "actions",
            header: "Actions",
            cell: ({ row }) => (
                <RequestActionsCell
                    row={row.original}
                    isLoading={loadingRow?.id === row.original.id && loadingRow.type === "action"}
                    onAccept={handleAccept}
                    onRefuse={handleRefuse}
                />
            ),
        },
    ], [loadingRow, handleDownload, handlePreview, handleAccept, handleRefuse]);

    return (
        <div className="space-y-6">
            <Breadcrumbs />
            <h1 className="text-2xl font-semibold mr-4" >Requests property</h1>
            {requests.length === 0 ? (
                <div className="rounded-lg border border-dashed border-base-200 bg-base-100 p-8 text-center text-base-content/70">
                    No waiting requests property.
                </div>
            ) : (
                <GenericTable<RequestPropertyRow> data={requests} columns={columns} className="mt-4" />
            )}
        </div>
    );
};

export default AdminRequestProperty;
