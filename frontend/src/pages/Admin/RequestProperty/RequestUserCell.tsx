import React from "react";
import {RequestPropertyRow} from "./useRequestProperty";

export const RequestUserCell: React.FC<{ row: RequestPropertyRow }> = ({ row }) => (
    <div className="flex flex-col">
        <span className="font-semibold">{row.username}</span>
        <span className="text-sm text-base-content/70">{row.userEmail}</span>
        <span className="text-xs text-base-content/60">{row.userRole}</span>
    </div>
);
