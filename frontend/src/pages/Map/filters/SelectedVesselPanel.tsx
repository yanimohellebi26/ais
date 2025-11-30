import React, { useEffect, useState } from "react";
import { Search, RefreshCcw, Calendar, Ship, ArrowRight } from "lucide-react";
import { toast } from "react-toastify";
import { useApi } from "../../../hooks/useApi";
import { Vessel } from "../../Ships/ShipsList/interfaces";
import { useNavigate } from "react-router-dom";
import { isValidDateFormat } from "../utils/dateValidation";

interface SelectedVesselPanelProps {
    vesselId: number;
    initialDate?: string;
    initialRadiusKm?: number;
    onSearch?: (date?: string, radiusKm?: number) => void;
    onReset?: () => void;
}

const SelectedVesselPanel: React.FC<SelectedVesselPanelProps> = ({
                                                                     vesselId,
                                                                     initialDate,
                                                                     initialRadiusKm,
                                                                     onSearch,
                                                                     onReset,
                                                                 }) => {
    const navigate = useNavigate();
    const api = useApi();
    const [vessel, setVessel] = useState<Vessel>();
    const [dateInput, setDateInput] = useState<string>(initialDate ?? "");
    const [radiusKm, setRadiusKm] = useState<number>(initialRadiusKm ?? 50);

    useEffect(() => {
        const fetchVessel = async () => {
            if (!vesselId) return;
            try {
                const data = await api(`/api/v1/vessels/${vesselId}`);
                setVessel(data);
            } catch (err: any) {
                toast.error(err.message || "Error while retrieving vessels");
            }
        };
        fetchVessel();
    }, [vesselId, api]);

    useEffect(() => {
        setDateInput(initialDate ?? "");
    }, [initialDate]);

    useEffect(() => {
        setRadiusKm(initialRadiusKm ?? 50);
    }, [initialRadiusKm]);

    const handleSearch = () => {
        if (!isValidDateFormat(dateInput)) {
            toast.error("Invalid date format. Use yyyy-MM-dd or yyyy-MM-dd HH:mm:ss");
            return;
        }
        onSearch?.(dateInput.trim() || undefined, radiusKm);
    };

    const handleReset = () => {
        onReset?.();
    };

    const navigateToVesselDetails = () => {
        navigate(`/dashboard/ships/details/${vesselId}`, {
            state: { vessel },
        });
    };

    return (
        <div className="p-5 border border-base-300 rounded-xl bg-base-200 shadow-inner">
            <h3 className="font-bold text-base mb-3 flex items-center gap-2">
                <Ship className="w-4 h-4 text-primary" />
                Selected vessel
                <span className="badge badge-primary badge-sm">{vesselId}</span>
                <button className="btn btn-ghost btn-xs" onClick={navigateToVesselDetails}>
                    <ArrowRight className="w-4 h-4" />
                </button>
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
                    onClick={handleSearch}
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
    );
};

export default SelectedVesselPanel;