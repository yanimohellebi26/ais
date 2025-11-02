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
