import React, {useEffect, useState} from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

interface MapFilterDrawerProps {
    children?: React.ReactNode;
    selectedVesselMmsi?: string;
    targetDate?: string;
    targetRadiusKm?: number;
    onFetchNearbyVessels?: (date?: string, radiusKm?: number) => void;
    resetSelectedVessel?: () => void;
}

const MapFilterDrawer: React.FC<MapFilterDrawerProps> = ({ children, selectedVesselMmsi, targetDate, targetRadiusKm, onFetchNearbyVessels, resetSelectedVessel, }) => {
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
        if(!selectedVesselMmsi) return;
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
                    {selectedVesselMmsi && (
                        <div className="p-4 border border-base-300 rounded-lg bg-base-200">
                            <h3 className="font-semibold mb-2">Selected vessel</h3>
                            <p>MMSI : {selectedVesselMmsi}</p>

                            <div className="mt-4 flex flex-col gap-2">
                                <label className="font-medium">Date (optional)</label>
                                <input
                                    type="text"
                                    placeholder="yyyy-MM-dd or yyyy-MM-dd HH:mm:ss"
                                    value={dateInput}
                                    onChange={(e) => setDateInput(e.target.value)}
                                    className="input input-bordered w-full"
                                />

                                <label className="font-medium mt-2">Radius (km)</label>
                                <input
                                    type="range"
                                    min={1}
                                    max={500}
                                    value={radiusKm}
                                    className="range range-primary"
                                    onChange={(e) => setRadiusKm(Number(e.target.value))}
                                />
                                <div className="text-sm text-gray-500">Current value : {radiusKm} km</div>

                                <button
                                    className="btn btn-primary mt-2"
                                    onClick={handleFetch}
                                >
                                    Search for nearby vessels
                                </button>

                                <button
                                    className="btn btn-primary mt-2"
                                    onClick={handleReset}
                                >
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
