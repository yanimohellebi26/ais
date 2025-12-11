import { DateRange } from "react-day-picker";
import { MAP_STYLES } from "../constants/mapStyles";

export type MapStyleType = typeof MAP_STYLES[keyof typeof MAP_STYLES];

export interface PortGeoJson {
    portId: number;
    name: string;
    code: string;
    country: string;
}

export interface VesselGeoJson {
    vesselName: string
    vesselId: number;
    mmsi: string;
    sog: number;
    cog: number;
    heading: number;
    status: string;
    baseDateTime: string;
    distanceKm?: number;
}

export interface MapFilters {
    limit: number;
    dateRange?: DateRange;
    showPorts: boolean;
}

export interface VesselSelection {
    vesselId: number | null;
    positionId: number | null;
    targetDate?: string;
    targetRadiusKm?: number;
}

export interface TooltipData<T> {
    data: T;
    x: number;
    y: number;
}