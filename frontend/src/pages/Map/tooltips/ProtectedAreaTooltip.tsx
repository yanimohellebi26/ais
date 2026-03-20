import React from 'react';

interface Props {
    data: any;
    x: number;
    y: number;
}

const ProtectedAreaTooltip: React.FC<Props> = ({ data, x, y }) => {
    return (
        <div 
            className="fixed z-[100] p-3 bg-base-100 border border-accent rounded-lg shadow-xl pointer-events-none text-xs min-w-[200px]"
            style={{ left: x + 10, top: y + 10 }}
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