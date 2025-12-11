import React, {JSX} from "react";
import Card from "../../../../components/BaseComponents/Card";
import {Vessel} from "../../interfaces";

interface Props {
    vessel: Vessel;
}

const ShipCards: React.FC<Props> = ({vessel}) => {
    const displayValue = (value: any, suffix: string = ""): JSX.Element => {
        if (value === null || value === undefined || value === "") {
            return <span className="text-gray-400 italic">Unknown</span>;
        }
        return <span>{value}{suffix}</span>;
    };

    // Format date
    const formatDateTime = (dateString: string): string => {
        if (!dateString) return "Unknown";

        const date = new Date(dateString);

        return date.toLocaleString('fr-FR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    // Check for captain
    const hasCaptain = vessel.users.some(user => user.role === "CAPTAIN");
    const captain = vessel.users.find(user => user.role === "CAPTAIN");

    return (
        <>
            <Card>
                <div className="p-6 space-y-2">
                    <p><strong>MMSI:</strong> {displayValue(vessel.mmsi)}</p>
                    <p><strong>IMO:</strong> {displayValue(vessel.imo)}</p>
                    <p><strong>Country:</strong> {displayValue(vessel.country)}</p>
                </div>
            </Card>

            <Card>
                <div className="p-6 space-y-2">
                    <p><strong>Call Sign:</strong> {displayValue(vessel.callSign)}</p>
                    <p><strong>Vessel Type:</strong> {displayValue(vessel.vesselTypeName)}</p>
                    <p><strong>Cargo Type:</strong> {displayValue(vessel.cargoTypeName)}</p>
                </div>
            </Card>

            <Card>
                <div className="p-6 space-y-2">
                    <p><strong>Draft:</strong> {displayValue(vessel.draft, "m")}</p>
                    <p><strong>Dimensions:</strong> {
                        vessel.length && vessel.width
                            ? `${vessel.length}m × ${vessel.width}m`
                            : "Unknown"
                    }</p>
                    <p><strong>Transceiver:</strong> {displayValue(vessel.transceiverClass)}</p>
                </div>
            </Card>

            <Card>
                <div className="p-6 space-y-2">
                    <p><strong>Captain:</strong>
                        <span className={`badge ${hasCaptain ? "badge-primary" : "badge-error"} ml-2`}>
                            {hasCaptain ? captain?.username : "No Captain"}
                        </span>
                    </p>
                    <p><strong>Last Update:</strong><br/>{formatDateTime(vessel.baseDateTime)}</p>
                </div>
            </Card>
        </>
    );
};

export default ShipCards;