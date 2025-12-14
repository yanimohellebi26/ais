import { useState } from "react";
import { DateRange } from "react-day-picker";

export const useMapFilters = () => {
    const [styleIndex, setStyleIndex] = useState(0);
    const [limit, setLimit] = useState(500);
    const [isFullscreen, setIsFullscreen] = useState(false);
    const [selectedRange, setSelectedRange] = useState<DateRange | undefined>();
    const [showPorts, setShowPorts] = useState(true);
    const [selectedVesselId, setSelectedVesselId] = useState<number | null>(null);
    const [selectedPositionId, setSelectedPositionId] = useState<number | null>(null);
    const [targetDate, setTargetDate] = useState<string | undefined>();
    const [targetRadiusKm, setTargetRadiusKm] = useState<number | undefined>();

    const handleVesselClick = (vesselId: number, positionId: number, targetDate: string) => {
        setSelectedVesselId(vesselId);
        setSelectedPositionId(positionId);
        setTargetDate(targetDate);
        setTargetRadiusKm(50);
    };

    const handleUpdateFilters = (date?: string, radiusKm?: number) => {
        setTargetDate(date);
        setTargetRadiusKm(radiusKm);
    };

    const handleReset = () => {
        setSelectedVesselId(null);
        setSelectedPositionId(null);
        setTargetDate(undefined);
        setTargetRadiusKm(undefined);
    };

    return {
        // States
        styleIndex,
        limit,
        isFullscreen,
        selectedRange,
        showPorts,
        selectedVesselId,
        selectedPositionId,
        targetDate,
        targetRadiusKm,
        // Setters
        setStyleIndex,
        setLimit,
        setIsFullscreen,
        setSelectedRange,
        setShowPorts,
        // Handlers
        handleVesselClick,
        handleUpdateFilters,
        handleReset
    };
};