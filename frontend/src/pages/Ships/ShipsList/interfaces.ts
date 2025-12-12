export interface Vessel {
    id: number;
    mmsi: string;
    imo: string | null;
    vesselName: string;
    callSign: string | null;
    vesselType: number | null;
    vesselTypeName: string;
    cargoType: number | null;
    cargoTypeName: string;
    length: number | null;
    width: number | null;
    draft: number | null;
    transceiverClass: string | null;
    locked: boolean;
    baseDateTime: string;
}

export interface VesselFilters {
    country?: string;
    minLength?: number;
    maxLength?: number;
    minWidth?: number;
    maxWidth?: number;
    minDraft?: number;
    maxDraft?: number;
    search?: string;
    vesselType?: number;
    vesselGroup?: string;
}

export interface Country {
    name: string;
    alpha2: string;
    alpha3: string;
    mid: number;
}

export interface VesselType {
    code : number;
    description: string;
    vesselGroup: string;
}
