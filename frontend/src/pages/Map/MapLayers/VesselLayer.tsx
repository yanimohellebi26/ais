import React from "react";
import { Source, Layer, useMap } from "@vis.gl/react-maplibre";
import {useVesselPositions} from "../../../hooks/useVesselPositions";
import {DateRange} from "react-day-picker";

interface Props {
    limit?: number;
    dateRange?: DateRange;
}

const VesselLayer: React.FC<Props> = ({ limit, dateRange }) => {
    const { current: map } = useMap();
    const geoJson = useVesselPositions({ map, limit, dateRange});

    if (!geoJson) return null;

    return (
        <Source
            id="vessels-source"
            type="geojson"
            data={geoJson}
            cluster={true}
            clusterRadius={50}
            clusterMaxZoom={6}
        >
            {/* Cluster circles */}
            <Layer
                id="clusters"
                type="circle"
                filter={["has", "point_count"]}
                paint={{
                    "circle-color": [
                        "step",
                        ["get", "point_count"],
                        "#51bbd6", 10,
                        "#3b84aa", 30,
                        "#032f53",
                    ],
                    "circle-radius": ["step", ["get", "point_count"], 15, 10, 20, 30, 25],
                }}
            />

            {/* Cluster count labels */}
            <Layer
                id="cluster-count"
                type="symbol"
                filter={["has", "point_count"]}
                layout={{
                    "text-field": "{point_count_abbreviated}",
                    "text-font": ["Open Sans Bold"],
                    "text-size": 12
                }}
                paint={{
                    "text-color": "#ffffff",
                }}
            />


            {/* Individual points */}
            <Layer
                id="unclustered-point"
                type="circle"
                filter={["!", ["has", "point_count"]]}
                paint={{
                    "circle-radius": 6,
                    "circle-color": "#007BFF",
                    "circle-stroke-width": 2,
                    "circle-stroke-color": "#FFFFFF",
                }}
            />
        </Source>
    );
};

export default VesselLayer;
