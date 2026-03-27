import React, { useEffect, useRef, useState } from 'react';
import { Shield } from "lucide-react";

interface Props {
    data: any;
    x: number;
    y: number;
    placement?: "top" | "bottom";
    color? : string;
}

const ProtectedAreaTooltip: React.FC<Props> = ({ data, x, y, placement = "top", color = "#555555"}) => {
    const ref = useRef<HTMLDivElement>(null);
    const [size, setSize] = useState({ width: 0, height: 0 });

    useEffect(() => {
        if (ref.current) {
            setSize({ width: ref.current.offsetWidth, height: ref.current.offsetHeight });
        }
    }, [data]);

    const OFFSET = 12;

    const { left, top } = placement === "bottom" ? { left: x - size.width - OFFSET, top: y + OFFSET }
                                                 : { left: x, top: y - size.height - OFFSET };
    return (
        <div
            ref={ref}
            style={{ position: "fixed", left: left, top: top, pointerEvents: "none", zIndex: 1000 }}
        >
            <div className="card bg-base-100 shadow-xl w-64 overflow-hidden">
                {/* Header */}
                <div className="px-4 py-2 flex items-center gap-2" style={{ backgroundColor: color }}>
                    <Shield className="w-4 h-4 text-white" />
                    <span className="font-bold text-sm text-white flex-1 truncate">{data.name}</span>
                    <div className="badge badge-sm text-white font-mono font-bold border-white/40 bg-white/20">
                        {data.iucn_cat}
                    </div>
                </div>

                <div className="card-body p-3 gap-1">
                    <div className="flex justify-between items-center">
                        <span className="text-xs text-base-content/50">Type</span>
                        <span className="text-xs font-medium">{data.site_type}</span>
                    </div>
                    <div className="flex justify-between items-center">
                        <span className="text-xs text-base-content/50">Designation</span>
                        <span className="text-xs font-medium text-right max-w-[60%] truncate">{data.desig_eng}</span>
                    </div>
                    <div className="flex justify-between items-center">
                        <span className="text-xs text-base-content/50">Status</span>
                        <span className="text-xs font-medium">{data.status} <span className="text-base-content/40">({data.status_yr})</span></span>
                    </div>
                    <div className="flex justify-between items-center">
                        <span className="text-xs text-base-content/50">Realm</span>
                        <span className="text-xs font-medium">{data.realm}</span>
                    </div>
                    <div className="divider my-0" />
                    <div className="flex justify-between items-center">
                        <span className="text-xs text-base-content/50">Country</span>
                        <div className="badge badge-outline badge-sm">{data.iso3}</div>
                    </div>
                    <div className="flex justify-between items-center">
                        <span className="text-xs text-base-content/50">No Take</span>
                        <div className={`badge badge-sm ${data.no_take === 'All' ? 'badge-success' : data.no_take === 'None' ? 'badge-error' : 'badge-warning'}`}>
                            {data.no_take}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ProtectedAreaTooltip;