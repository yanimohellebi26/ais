import React, { useRef, useEffect, useState } from "react";
import { MapPin, Activity } from "lucide-react";

interface Props {
    data: {
        density: number;
        lat: number;
        lon: number;
    };
    x: number;
    y: number;
}

const TrafficDensityTooltip: React.FC<Props> = ({ data, x, y }) => {
    const ref = useRef<HTMLDivElement>(null);
    const [size, setSize] = useState({ width: 0, height: 0 });

    useEffect(() => {
        if (ref.current) {
            setSize({
                width: ref.current.offsetWidth,
                height: ref.current.offsetHeight
            });
        }
    }, [data]);

    const OFFSET = 10;

    const left = x;
    const top = y - size.height - OFFSET;

    return (
        <div
            ref={ref}
            style={{
                position: "fixed",
                left,
                top,
                pointerEvents: "none",
                zIndex: 1000
            }}
        >
            <div className="card bg-base-100 shadow-xl w-56 overflow-hidden">
                {/* Header */}
                <div className="px-3 py-2 bg-primary text-primary-content flex items-center gap-2">
                    <Activity className="w-4 h-4" />
                    <span className="font-semibold text-sm">
                        Density
                    </span>
                </div>

                {/* Content */}
                <div className="card-body p-3 text-xs gap-2">

                    <div className="flex justify-between">
                        <span className="text-base-content/60">Vessels</span>
                        <span className="font-bold">{data.density}</span>
                    </div>

                    <div className="divider my-1" />

                    <div className="flex items-center gap-2">
                        <MapPin className="w-3.5 h-3.5 text-error" />
                        <span>Lat:</span>
                        <span className="ml-auto font-mono">
                            {data.lat.toFixed(1)}
                        </span>
                    </div>

                    <div className="flex items-center gap-2">
                        <MapPin className="w-3.5 h-3.5 text-info" />
                        <span>Lon:</span>
                        <span className="ml-auto font-mono">
                            {data.lon.toFixed(1)}
                        </span>
                    </div>

                </div>
            </div>
        </div>
    );
};

export default TrafficDensityTooltip;