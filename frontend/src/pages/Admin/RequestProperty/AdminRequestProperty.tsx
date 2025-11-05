import React, { useCallback, useEffect, useMemo, useState } from "react";
import Breadcrumbs from "../../../components/BaseComponents/Breadcrumbs";
import TitleH1 from "../../../components/BaseComponents/TitleH1";
import { GenericTable } from "../../../components/BaseComponents/GenericTable";
import Button from "../../../components/BaseComponents/Button";
import { useApi, API_BASE_URL } from "../../../hooks/useApi";
import { PageResponse, RequestPropertyAdmin } from "../../../types";
import { toast } from "react-toastify";
import { useAuth } from "../../../context/AuthContext";
import Swal from "sweetalert2";
import withReactContent from "sweetalert2-react-content";
import { ColumnDef } from "@tanstack/react-table";
import { Download, Eye, Loader2 } from "lucide-react";

const MySwal = withReactContent(Swal);

type RequestPropertyRow = {
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

const AdminRequestProperty: React.FC = () => {
    const api = useApi();
    const { user } = useAuth();

    const [requests, setRequests] = useState<RequestPropertyRow[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [actionId, setActionId] = useState<number | null>(null);
    const [downloadingId, setDownloadingId] = useState<number | null>(null);
    const [previewingId, setPreviewingId] = useState<number | null>(null);

    const fetchRequests = useCallback(async () => {
        setIsLoading(true);
        try {
            const page = await api<PageResponse<RequestPropertyAdmin>>("/api/v1/request-property");
            setRequests(page.content.map(mapToRow));
        } catch (error) {
            toast.error("Failed to load request properties");
        } finally {
            setIsLoading(false);
        }
    }, [api]);

    useEffect(() => {
        fetchRequests();
    }, [fetchRequests]);

    const handleDownload = useCallback(async (row: RequestPropertyRow) => {
        if (!API_BASE_URL) {
            toast.error("Missing API configuration");
            return;
        }

        setDownloadingId(row.id);
        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/uploads/${row.fileId}/download`, {
                headers: user?.token ? { Authorization: `Bearer ${user.token}` } : undefined,
            });

            if (!response.ok) {
                throw new Error("Download failed");
            }

            const blob = await response.blob();
            const disposition = response.headers.get("Content-Disposition");
            let filename = row.fileName;

            if (disposition) {
                const match = disposition.match(/filename\*=UTF-8''([^;]+)|filename="?([^";]+)"?/i);
                const extracted = match?.[1] || match?.[2];
                if (extracted) {
                    filename = decodeURIComponent(extracted);
                }
            }

            const blobUrl = URL.createObjectURL(blob);
            const link = document.createElement("a");
            link.href = blobUrl;
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            link.remove();
            URL.revokeObjectURL(blobUrl);
            toast.success(`File ${filename} downloaded`);
        } catch (error) {
            toast.error("Unable to download file");
        } finally {
            setDownloadingId(null);
        }
    }, [user]);

    const handlePreview = useCallback(async (row: RequestPropertyRow) => {
        if (!API_BASE_URL) {
            toast.error("Missing API configuration");
            return;
        }

        setPreviewingId(row.id);
        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/uploads/${row.fileId}/download`, {
                headers: user?.token ? { Authorization: `Bearer ${user.token}` } : undefined,
            });

            if (!response.ok) {
                throw new Error("Preview failed");
            }

            const blob = await response.blob();
            const blobUrl = URL.createObjectURL(blob);
            
            // Créer une nouvelle fenêtre avec un document HTML qui contient un iframe pour le PDF
            const viewer = window.open("", "_blank", "noopener,noreferrer");
            if (!viewer) {
                URL.revokeObjectURL(blobUrl);
                throw new Error("Unable to open preview window");
            }

            // Écrire le HTML dans la nouvelle fenêtre pour afficher le PDF
            viewer.document.write(`
                <!DOCTYPE html>
                <html>
                <head>
                    <title>${row.fileName}</title>
                    <style>
                        body, html {
                            margin: 0;
                            padding: 0;
                            width: 100%;
                            height: 100%;
                            overflow: hidden;
                        }
                        iframe {
                            border: none;
                            width: 100%;
                            height: 100%;
                        }
                    </style>
                </head>
                <body>
                    <iframe src="${blobUrl}" type="application/pdf"></iframe>
                </body>
                </html>
            `);
            viewer.document.close();

            // Nettoyer l'URL après un délai
            setTimeout(() => URL.revokeObjectURL(blobUrl), 60_000);
        } catch (error) {
            toast.error("Impossible d'ouvrir le fichier");
        } finally {
            setPreviewingId(null);
        }
    }, [user]);

    const removeRequestFromState = useCallback((id: number) => {
        setRequests(prev => prev.filter(item => item.id !== id));
    }, []);

    const handleAccept = useCallback(async (row: RequestPropertyRow) => {
        const confirm = await MySwal.fire({
            title: `Accept ownership for ${row.username}?`,
            text: "The user will become owner of the vessel",
            icon: "question",
            showCancelButton: true,
            confirmButtonText: "Accept",
            cancelButtonText: "Cancel",
        });

        if (!confirm.isConfirmed) return;

        setActionId(row.id);
        try {
            await api("/api/v1/vessels/related", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ userId: row.userId, mmsi: row.mmsi })
            });

            await api(`/api/v1/request-property/${row.id}`, {
                method: "DELETE",
            });

            toast.success("Request accepted");
            removeRequestFromState(row.id);
        } catch (error) {
            toast.error("Failed to accept the request");
        } finally {
            setActionId(null);
        }
    }, [api, removeRequestFromState]);

    const handleRefuse = useCallback(async (row: RequestPropertyRow) => {
        const confirm = await MySwal.fire({
            title: `Refuse ownership for ${row.username}?`,
            text: "The associated file will be deleted",
            icon: "warning",
            showCancelButton: true,
            confirmButtonText: "Refuse",
            cancelButtonText: "Cancel",
        });

        if (!confirm.isConfirmed) return;

        setActionId(row.id);
        try {
            await api(`/api/v1/request-property/${row.id}`, {
                method: "DELETE",
            });
            toast.success("Request refused");
            removeRequestFromState(row.id);
        } catch (error) {
            toast.error("Failed to refuse the request");
        } finally {
            setActionId(null);
        }
    }, [api, removeRequestFromState]);

    const columns = useMemo<ColumnDef<RequestPropertyRow>[]>(() => [
        {
            id: "user",
            header: "Utilisateur",
            cell: ({ row }) => (
                <div className="flex flex-col">
                    <span className="font-semibold">{row.original.username}</span>
                    <span className="text-sm text-base-content/70">{row.original.userEmail}</span>
                    <span className="text-xs text-base-content/60">{row.original.userRole}</span>
                </div>
            ),
        },
        {
            accessorKey: "mmsi",
            header: "MMSI",
        },
        {
            id: "createdAt",
            header: "Date",
            cell: ({ row }) => new Date(row.original.createdAt).toLocaleString(),
        },
        {
            id: "file",
            header: "Fichier",
            cell: ({ row }) => (
                <div className="flex flex-col gap-1">
                    <button
                        className="btn btn-link btn-sm px-0 justify-start"
                        onClick={() => handleDownload(row.original)}
                        disabled={downloadingId === row.original.id}
                    >
                        {downloadingId === row.original.id ? (
                            <span className="flex items-center gap-1"><Loader2 className="h-4 w-4 animate-spin" /> Téléchargement...</span>
                        ) : (
                            <span className="flex items-center gap-1"><Download className="h-4 w-4" /> Télécharger</span>
                        )}
                    </button>
                    <button
                        className="btn btn-link btn-sm px-0 justify-start"
                        onClick={() => handlePreview(row.original)}
                        disabled={previewingId === row.original.id}
                    >
                        {previewingId === row.original.id ? (
                            <span className="flex items-center gap-1"><Loader2 className="h-4 w-4 animate-spin" /> Ouverture...</span>
                        ) : (
                            <span className="flex items-center gap-1"><Eye className="h-4 w-4" /> Voir le PDF</span>
                        )}
                    </button>
                </div>
            ),
        },
        {
            id: "actions",
            header: "Actions",
            cell: ({ row }) => (
                <div className="flex gap-2">
                    <Button
                        className="btn btn-success btn-sm"
                        onClick={() => handleAccept(row.original)}
                        disabled={actionId === row.original.id}
                    >
                        {actionId === row.original.id ? <Loader2 className="h-4 w-4 animate-spin" /> : "Accepter"}
                    </Button>
                    <Button
                        className="btn btn-error btn-sm"
                        onClick={() => handleRefuse(row.original)}
                        disabled={actionId === row.original.id}
                    >
                        {actionId === row.original.id ? <Loader2 className="h-4 w-4 animate-spin" /> : "Refuser"}
                    </Button>
                </div>
            ),
        },
    ], [actionId, downloadingId, handleAccept, handleDownload, handlePreview, handleRefuse, previewingId]);

    return (
        <div className="space-y-6">
            <Breadcrumbs />
            <TitleH1>Demandes de propriété</TitleH1>

            {isLoading ? (
                <div className="flex h-40 items-center justify-center text-base-content/70">
                    <Loader2 className="h-6 w-6 animate-spin" />
                </div>
            ) : requests.length === 0 ? (
                <div className="rounded-lg border border-dashed border-base-200 bg-base-100 p-8 text-center text-base-content/70">
                    Aucune demande en attente.
                </div>
            ) : (
                <GenericTable<RequestPropertyRow> data={requests} columns={columns} className="mt-4" />
            )}
        </div>
    );
};

export default AdminRequestProperty;
