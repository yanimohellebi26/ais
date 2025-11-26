import React, {useState} from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import SelectedVesselPanel from "../../components/BaseComponents/SelectedVesselPanel";

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

    const handleFetch = (date?: string, radius?: number) => {
        if(!selectedVesselId) return;
        onFetchNearbyVessels?.(date, radius);
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
                        <SelectedVesselPanel
                            vesselId={selectedVesselId}
                            initialDate={targetDate}
                            initialRadiusKm={targetRadiusKm}
                            onSearch={handleFetch}
                            onReset={handleReset}
                        />
                    )}
                    {children}
                </div>
            )}
        </aside>
    );
};

export default MapFilterDrawer;
