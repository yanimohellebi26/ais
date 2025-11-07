import React from "react";
import { Loader2 } from "lucide-react";
import {RequestPropertyRow} from "./useRequestProperty";
import Button from "../../../components/BaseComponents/Button";

type Props = {
    row: RequestPropertyRow;
    isLoading: boolean;
    onAccept: (row: RequestPropertyRow) => void;
    onRefuse: (row: RequestPropertyRow) => void;
};

export const RequestActionsCell: React.FC<Props> = ({ row, isLoading, onAccept, onRefuse }) => (
    <div className="flex gap-2">
        <Button className="btn btn-success btn-sm" onClick={() => onAccept(row)} disabled={isLoading}>
            {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Accept"}
        </Button>
        <Button className="btn btn-error btn-sm" onClick={() => onRefuse(row)} disabled={isLoading}>
            {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Refuse"}
        </Button>
    </div>
);
