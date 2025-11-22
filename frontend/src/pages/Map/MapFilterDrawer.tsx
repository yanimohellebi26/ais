import React, {useEffect, useState} from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Search, RefreshCcw, Calendar, Ship } from "lucide-react";

interface MapFilterDrawerProps {
    children?: React.ReactNode;
    selectedVesselId?: number;
    targetDate?: string;
    targetRadiusKm?: number;
    onFetchNearbyVessels?: (date?: string, radiusKm?: number) => void;
    resetSelectedVessel?: () => void;
}

const MapFilterDrawer: React.FC<MapFilterDrawerProps> = ({ children, selectedVesselId, targetDate, targetRadiusKm, onFetchNearbyVessels, resetSelectedVessel, }) => {
    const [collapsed, setCollapsed] = useState(false);
    const [dateInput, setDateInput] = useState<string>(targetDate ?? "");
    const [radiusKm, setRadiusKm] = useState<number>(targetRadiusKm ?? 50);

    useEffect(() => {
        setDateInput(targetDate ?? "");
    }, [targetDate]);

    useEffect(() => {
        setRadiusKm(targetRadiusKm ?? 50);
    }, [targetRadiusKm]);

    const handleFetch = () => {
        if(!selectedVesselId) return;
        onFetchNearbyVessels?.(dateInput.trim() || undefined, radiusKm);
    };

    const handleReset = () => {
        resetSelectedVessel?.();
    };

    return (
        <aside
            className={`z-10 fixed top-10 h-[90vh] rounded-tl-2xl rounded-bl-2xl bg-base-100 shadow-lg transition-all duration-300 flex flex-col
        ${collapsed ? "right-[-25rem]" : "right-0"} w-100`}
        >
            <div className="flex items-center justify-between p-4 border-b border-base-300 relative">
                {!collapsed && <h2 className="text-lg font-semibold ">Options & Filters</h2>}

                <button
                    onClick={() => setCollapsed(!collapsed)}
                    className="btn btn-ghost btn-sm absolute -left-10 top-1/2 -translate-y-1/2 rounded-l-2xl bg-base-100"
                >
                    {collapsed ? <ChevronLeft /> : <ChevronRight />}
                </button>
            </div>

            {!collapsed && (
                <div className="flex-1 flex flex-col gap-4 p-4 overflow-y-auto">
                    {/* Selected vessel section */}
                    {selectedVesselId && (
                        <div className="p-5 border border-base-300 rounded-xl bg-base-200 shadow-inner">
                            <h3 className="font-bold text-base mb-3 flex items-center gap-2">
                                <Ship className="w-4 h-4 text-primary" />
                                Selected vessel
                                <span className="badge badge-primary badge-sm">{selectedVesselId}</span>
                            </h3>

                            {/* Date Input */}
                            <div className="form-control w-full">
                                <label className="label">
                                    <Calendar className="w-4 h-4 opacity-70" />
                                    <span className="label-text font-medium">Date (optional)</span>
                                </label>
                                <input
                                    type="text"
                                    placeholder="yyyy-MM-dd or yyyy-MM-dd HH:mm:ss"
                                    value={dateInput}
                                    onChange={(e) => setDateInput(e.target.value)}
                                    className="input input-bordered input-sm w-full"
                                />
                            </div>
                            {/* Radius range */}
                            <div className="form-control w-full mt-4">
                                <label className="label">
                                    <span className="label-text font-medium">Radius (km)</span>
                                </label>
                                <input
                                    type="range"
                                    min={1}
                                    max={500}
                                    value={radiusKm}
                                    className="range range-primary range-sm"
                                    onChange={(e) => setRadiusKm(Number(e.target.value))}
                                />
                                <div className="text-xs mt-1 text-gray-500 text-right">
                                    Current value: <span className="font-semibold">{radiusKm} km</span>
                                </div>
                            </div>
                            <div className="mt-5 flex flex-col gap-2">

                                <button
                                    className="btn btn-primary btn-sm w-full"
                                    onClick={handleFetch}
                                >
                                    <Search className="w-4 h-4" />
                                    Search for nearby vessels
                                </button>

                                <button
                                    className="btn btn-outline btn-error btn-sm w-full"
                                    onClick={handleReset}
                                >
                                    <RefreshCcw className="w-4 h-4" />
                                    Reset
                                </button>
                            </div>
                        </div>
                    )}
                    {children}
                </div>
            )}
        </aside>
    );
};

export default MapFilterDrawer;
