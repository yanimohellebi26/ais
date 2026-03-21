import React, { useEffect, useRef, useState } from 'react';

interface Props {
    data: any;
    x: number;
    y: number;
    placement?: "top" | "bottom";
}

const ProtectedAreaTooltip: React.FC<Props> = ({ data, x, y, placement = "top"}) => {
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
            className="fixed z-[100] p-3 bg-base-100 border border-accent rounded-lg shadow-xl pointer-events-none text-xs min-w-[200px]"
            style={{ left: left, top: top }}
        >
            <div className="font-bold text-sm mb-1 border-b border-base-300 pb-1">{data.name} <span className="text-secondary">({data.iso3})</span></div>
            <div className="grid grid-cols-2 gap-x-2 gap-y-1">
                <span className="opacity-70">Type:</span> <span>{data.site_type}</span>
                <span className="opacity-70">Designation:</span> <span>{data.desig_eng}</span>
                <span className="opacity-70">IUCN Cat:</span> <span className="font-mono font-bold">{data.iucn_cat}</span>
                <span className="opacity-70">Status:</span> <span>{data.status} ({data.status_yr})</span>
                <span className="opacity-70">Realm:</span> <span>{data.realm}</span>
                <span className="opacity-70">No Take:</span> <span>{data.no_take}</span>
            </div>
        </div>
    );
};

export default ProtectedAreaTooltip;