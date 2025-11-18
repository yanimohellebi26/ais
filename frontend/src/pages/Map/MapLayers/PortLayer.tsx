import React from "react";
import { Source, Layer, useMap } from "@vis.gl/react-maplibre";
import { usePortPositions } from "../../../hooks/usePortPositions";


const PortLayer: React.FC= () => {
    const { current: map } = useMap();
    const geoJson = usePortPositions({ map});

    if (!geoJson) return null;

    return (
        <Source
            id="ports-source"
            type="geojson"
            data={geoJson}
        >
            <Layer
                id="ports-symbol"
                type="circle"
                paint={{
                    "circle-radius": 2,
                    "circle-color": "#b81b6f",
                }}
            />
        </Source>
    );
};

export default PortLayer;
