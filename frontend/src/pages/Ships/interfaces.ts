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
    baseDateTime: string;
    locked: boolean;
    country: string;
    users: UserPublicDetails[];
}

export interface UserPublicDetails {
    id: number;
    username: string;
    email: string;
    role: string;
}

export type CaptainDetails = {
    id:number;
    username:string;
    email:string;
    role:string;
}