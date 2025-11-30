import React from "react";
import { Anchor, MapPin, Hash, Flag } from "lucide-react";
import { PortGeoJson } from "../types/map";
import { MapTooltip } from "./MapTooltip";

interface Props {
    data: PortGeoJson;
    x: number;
    y: number;
}

const PortTooltip: React.FC<Props> = ({ data, x, y }) => {
    return (
        <MapTooltip
            x={x}
            y={y}
            title="Port"
            icon={<Anchor className="w-4 h-4" />}
            headerClassName="bg-secondary text-secondary-content"
        >
            <div className="flex items-center gap-2">
                <MapPin className="w-3.5 h-3.5 text-secondary mt-0.5 flex-shrink-0" />
                <span className="text-base-content/60">Name</span>
                <span className="font-bold text-sm ml-auto">{data.name}</span>
            </div>

            <div className="flex items-center gap-2 pt-1">
                <Hash className="w-3.5 h-3.5 text-info" />
                <span className="text-base-content/60">Code:</span>
                <span className="font-semibold ml-auto font-mono">{data.code}</span>
            </div>

            <div className="flex items-center gap-2">
                <Flag className="w-3.5 h-3.5 text-accent" />
                <span className="text-base-content/60">Country:</span>
                <span className="font-semibold ml-auto">{data.country}</span>
            </div>

            <div className="pt-1 border-t border-base-300">
                <span className="text-[10px] text-base-content/40">
                  ID: {data.portId}
                </span>
            </div>
        </MapTooltip>
    );
};

export default PortTooltip;