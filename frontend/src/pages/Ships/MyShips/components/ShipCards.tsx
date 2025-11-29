import React from "react";
import Card from "../../../../components/BaseComponents/Card";
import {Vessel} from "../../interfaces";


interface Props {
    vessel: Vessel;
}

const ShipCards: React.FC<Props> = ({vessel}) => {
    return (
        <>
            <Card >
                <div className="p-6 space-y-2">
                    <p><strong>MMSI:</strong> {vessel.mmsi}</p>
                    <p><strong>IMO:</strong> {vessel.imo}</p>
                </div>
            </Card>

            <Card >
                <div className="p-6 space-y-2">
                    <p><strong>Call Sign:</strong> {vessel.callSign}</p>
                    <p><strong>Vessel Type:</strong> {vessel.vesselTypeName}</p>
                    <p><strong>Cargo Type:</strong> {vessel.cargoTypeName}</p>
                </div>
            </Card>
            <Card >
                <div className="p-6 space-y-2">
                    <p><strong>Draft:</strong> {vessel.draft}m</p>
                    <p><strong>Dimensions:</strong> {vessel.length}m × {vessel.width}m</p>
                    <p><strong>Transceiver:</strong> {vessel.transceiverClass}</p>
                </div>
            </Card>

            <Card >
                <div className="p-6 space-y-2">
                    <p><strong>Status:</strong>
                        <span className={`badge ${vessel.locked ? "badge-error" : "badge-success"} ml-2`}>
                                    {vessel.locked ? "Locked" : "Unlocked"}
                                </span>
                    </p>
                    <p><strong>Last Update:</strong><br/>{vessel.baseDateTime}</p>
                </div>
            </Card>
        </>
    );
};

export default ShipCards;
