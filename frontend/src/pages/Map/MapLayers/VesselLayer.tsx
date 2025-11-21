import React from "react";
import { Source, Layer, useMap } from "@vis.gl/react-maplibre";
import {useVesselPositions} from "../../../hooks/useVesselPositions";
import {useVesselPositionsRadius} from "../../../hooks/useVesselPositionsRadius";
import {DateRange} from "react-day-picker";
import {toast} from "react-toastify";

interface Props {
    limit?: number;
    dateRange?: DateRange;
    targetVesselId?: number;
    targetDate?: string;
    targetRadiusKm?: number;
    onVesselClick?: (vesselId: number) => void;
}

const VesselLayer: React.FC<Props> = ({ limit, dateRange, targetVesselId, targetDate, targetRadiusKm, onVesselClick }) => {
    const { current: map } = useMap();

    const radiusGeoJson = useVesselPositionsRadius({
        map,
        vesselId: targetVesselId ?? -1,
        date: targetDate,
        radiusKm: targetRadiusKm,
        enabled: targetVesselId != null
    });

    const normalGeoJson = useVesselPositions({
        map,
        limit,
        dateRange
    });

    const geoJson = targetVesselId ? radiusGeoJson : normalGeoJson;

    const handleClick = (e: any) => {
        if(!map) return;
        const features = map.queryRenderedFeatures(e.point, { layers: ["unclustered-point"]});
        const vesselId = features[0].properties?.vesselId;
        if(features.length && vesselId != null){
            onVesselClick?.(Number(vesselId));
        }
    };

    React.useEffect(() => {
        if(!map) return;
        map.on("click", handleClick);
        return () => {
            map.off("click", handleClick);
        };
    }, [map, onVesselClick]);

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
                    "circle-color": [
                        "case",
                        ["==", ["get", "vesselId"], targetVesselId ?? -1],
                        "#FF0000",
                        "#007BFF"
                    ],
                    "circle-stroke-width": 2,
                    "circle-stroke-color": "#FFFFFF",
                }}
            />
        </Source>
    );
};

export default VesselLayer;
