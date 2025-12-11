import React from "react";

interface MapTooltipProps {
    x: number;
    y: number;
    title: string;
    icon: React.ReactNode;
    headerClassName?: string;
    children: React.ReactNode;
}

export const MapTooltip: React.FC<MapTooltipProps> = ({
                                                          x,
                                                          y,
                                                          title,
                                                          icon,
                                                          headerClassName = "bg-primary text-primary-content",
                                                          children
                                                      }) => {
    return (
        <div
            style={{
                position: "absolute",
                left: x + 10,
                top: y + 10,
                pointerEvents: "none",
                zIndex: 1000
            }}
            className="bg-base-100 rounded-lg shadow-xl overflow-hidden min-w-[200px]"
        >
            {/* Header */}
            <div className={`px-3 py-2 flex items-center gap-2 ${headerClassName}`}>
                {icon}
                <span className="font-bold text-sm">{title}</span>
            </div>

            {/* Content */}
            <div className="p-3 space-y-2 text">
                {children}
            </div>
        </div>
    );
};