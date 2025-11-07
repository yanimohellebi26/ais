import React from "react";
import { Download, Eye, Loader2 } from "lucide-react";
import {RequestPropertyRow} from "./useRequestProperty";

type Props = {
    row: RequestPropertyRow;
    isLoading?: "download" | "preview" | null;
    onDownload: (row: RequestPropertyRow) => void;
    onPreview: (row: RequestPropertyRow) => void;
};

export const RequestFileCell: React.FC<Props> = ({ row, isLoading, onDownload, onPreview }) => (
    <div className="flex flex-col gap-1">
        <button
            className="btn btn-link btn-sm px-0 justify-start"
            onClick={() => onDownload(row)}
            disabled={isLoading === "download"}
        >
            {isLoading === "download" ? (
                <span className="flex items-center gap-1">
          <Loader2 className="h-4 w-4 animate-spin" /> Downloading...
        </span>
            ) : (
                <span className="flex items-center gap-1">
          <Download className="h-4 w-4" /> Download
        </span>
            )}
        </button>
        <button
            className="btn btn-link btn-sm px-0 justify-start"
            onClick={() => onPreview(row)}
            disabled={isLoading === "preview"}
        >
            {isLoading === "preview" ? (
                <span className="flex items-center gap-1">
          <Loader2 className="h-4 w-4 animate-spin" /> Opening...
        </span>
            ) : (
                <span className="flex items-center gap-1">
          <Eye className="h-4 w-4" /> Open PDF
        </span>
            )}
        </button>
    </div>
);
