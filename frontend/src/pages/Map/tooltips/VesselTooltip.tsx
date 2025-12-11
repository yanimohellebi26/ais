import React from "react";
import { Ship, Navigation, Gauge, Compass, Activity, Clock } from "lucide-react";
import { VesselGeoJson } from "../types/map";
import { MapTooltip } from "./MapTooltip";
import { formatDateTime } from "../utils/dateValidation";

interface Props {
    data: VesselGeoJson;
    x: number;
    y: number;
}

const VesselTooltip: React.FC<Props> = ({ data, x, y }) => {
    return (
        <MapTooltip
            x={x}
            y={y}
            title={`Vessel ${data?.vesselName}`}
            icon={<Ship className="w-4 h-4" />}
            headerClassName="bg-primary text-primary-content"
        >
            <div className="flex items-center gap-2">
                <Navigation className="w-3.5 h-3.5 text-info" />
                <span className="text-base-content/60">MMSI:</span>
                <span className="font-semibold ml-auto">{data?.mmsi}</span>
            </div>

            <div className="flex items-center gap-2">
                <Gauge className="w-3.5 h-3.5 text-success" />
                <span className="text-base-content/60">SOG:</span>
                <span className="font-semibold ml-auto">{data?.sog?.toFixed(1)} kn</span>
            </div>

            <div className="flex items-center gap-2">
                <Compass className="w-3.5 h-3.5 text-warning" />
                <span className="text-base-content/60">COG:</span>
                <span className="font-semibold ml-auto">{data?.cog?.toFixed(1)}°</span>
            </div>

            <div className="flex items-center gap-2">
                <Compass className="w-3.5 h-3.5 text-secondary" />
                <span className="text-base-content/60">Heading:</span>
                <span className="font-semibold ml-auto">{data?.heading}°</span>
            </div>

            <div className="flex items-center gap-2">
                <Activity className="w-3.5 h-3.5 text-error" />
                <span className="text-base-content/60">Status:</span>
                <span className="badge badge-sm badge-outline ml-auto">{data?.status}</span>
            </div>

            {data.distanceKm !== undefined && (
                <div className="flex items-center gap-2 pt-1 border-t border-base-300">
                    <Navigation className="w-3.5 h-3.5 text-accent" />
                    <span className="text-base-content/60">Distance:</span>
                    <span className="font-semibold ml-auto">{data?.distanceKm?.toFixed(2)} km</span>
                </div>
            )}

            <div className="flex items-center gap-2 pt-1 border-t border-base-300">
                <Clock className="w-3.5 h-3.5 text-base-content/40" />
                <span className="text-base-content/60 text-[10px]">
                    {formatDateTime(data?.baseDateTime)}
                </span>
                <span className="text-[10px] text-base-content/40 ml-auto">
                  ID: {data.vesselId}
                </span>
            </div>

        </MapTooltip>
    );
};

export default VesselTooltip;