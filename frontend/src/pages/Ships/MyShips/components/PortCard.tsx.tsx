import React from "react";
import { Port } from "../../interfaces";
import {Globe, MapPin, Map, Info} from "lucide-react";

interface Props {
    port: Port | undefined;
}

const PortCard: React.FC<Props> = ({ port }) => {
    if (!port) {
        return (
            <div className="alert alert-info">
                <Info />
                <span>No port found</span>
            </div>
        );
    }

    return (
        <div className="card-body">
            <h2 className="card-title text-2xl">
                Nearest port : {port.name}
                <div className="badge badge-primary">{port.code} </div>
                <span className="text-sm opacity-70" >{port.portId}</span>
            </h2>

            <div className="divider"></div>

            <div className="space-y-3">
                <div className="flex items-center gap-2">
                    <Globe className="text-primary w-4 h-4"/>
                    <div>
                        <div className="text-sm opacity-70">Country</div>
                        <div className="font-semibold">{port.country}</div>
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    <MapPin className="text-secondary w-4 h-4" />
                    <div>
                        <div className="text-sm opacity-70">Coordinates</div>
                        <div className="font-mono text-sm">
                            {port.latitude.toFixed(4)}°N, {port.longitude.toFixed(4)}°E
                        </div>
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    <Map className="text-success w-4 h-4"/>
                    <div>
                        <div className="text-sm opacity-70">Distance</div>
                        <div className="font-semibold">{port.distance.toFixed(2)} m</div>
                    </div>
                </div>

                <div className="divider"></div>
            </div>
        </div>
    );
};

export default PortCard;