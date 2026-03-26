import React from "react";
import { Ship} from "lucide-react";
import { MapTooltip } from "./MapTooltip";

interface TrafficDensityTooltipProps {
    x: number;
    y: number;
    density: number;
}

const TrafficDensityTooltip: React.FC<TrafficDensityTooltipProps> = ({ x, y, density }) => {
    return (
        <MapTooltip
            x={x}
            y={y}
            title="Zone"
            icon={<Ship className="w-4 h-4 text-red-500" />}
            headerClassName="bg-secondary text-secondary-content"
        >
            <div className="flex flex-col gap-2">
                <div className="flex items-center gap-2">
                    <span className="text-base-content/60">Vessels :</span>
                    <span className="font-semibold ml-auto">{density}</span>
                </div>
            </div>
        </MapTooltip>
    );
};

export default TrafficDensityTooltip;