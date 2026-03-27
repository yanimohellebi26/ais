import React from "react";
import { Source, Layer, useMap } from "@vis.gl/react-maplibre";
import { useTrafficDensity } from "../../../hooks/useTrafficDensity";
import { DateRange } from "react-day-picker";

interface Props {
    dateRange?: DateRange;
    gridSize?: number;
}

const TrafficDensityLayer: React.FC<Props> = ({ dateRange, gridSize }) => {
    const { current: map } = useMap();
    if (!map) return null;
    const geoJson = useTrafficDensity({ map, gridSize, dateRange });

    if (!geoJson || geoJson.features.length == 0) return null;

    return (
        <>
            <Source id="traffic-density" type="geojson" data={geoJson}>
                <Layer
                    id="traffic-heatmap"
                    type="heatmap"
                    paint={{
                        "heatmap-weight": [
                            "interpolate",
                            ["linear"],
                            ["get", "density"],
                            0, 0,
                            100, 1
                        ],
                        "heatmap-radius": [
                            "interpolate",
                            ["linear"],
                            ["zoom"],
                            0, 2,
                            9, 20
                        ],
                        "heatmap-intensity": [
                            "interpolate",
                            ["linear"],
                            ["zoom"],
                            0, 1,
                            9, 3
                        ],
                        "heatmap-color": [
                            "interpolate",
                            ["linear"],
                            ["heatmap-density"],
                            0, "rgba(33,102,172,0)",
                            0.2, "rgb(103,169,207)",
                            0.4, "rgb(209,229,240)",
                            0.6, "rgb(253,219,199)",
                            0.8, "rgb(239,138,98)",
                            1, "rgb(178,24,43)"
                        ],
                        "heatmap-opacity": [
                            "interpolate",
                            ["linear"],
                            ["zoom"],
                            7, 1,
                            9, 0
                        ]
                    }}
                />
                <Layer
                    id="traffic-points"
                    type="circle"
                    minzoom={7}
                    paint={{
                        "circle-radius": [
                            "interpolate",
                            ["linear"],
                            ["zoom"],
                            7,
                            [
                                "interpolate",
                                ["linear"],
                                ["get", "density"],
                                0, 1,
                                50, 4,
                                200, 8
                            ],
                            16,
                            [
                                "interpolate",
                                ["linear"],
                                ["get", "density"],
                                0, 5,
                                50, 10,
                                200, 20
                            ]
                        ],
                        "circle-color": [
                            "interpolate",
                            ["linear"],
                            ["get", "density"],
                            0, "rgba(33,102,172,0)",
                            10, "rgb(103,169,207)",
                            50, "rgb(209,229,240)",
                            100, "rgb(253,219,199)",
                            200, "rgb(239,138,98)",
                            500, "rgb(178,24,43)"
                        ],
                        "circle-stroke-color": "#fff",
                        "circle-stroke-width": 1,
                        "circle-opacity":[
                            "interpolate",
                            ["linear"],
                            ["zoom"],
                            7, 0,
                            8, 1
                        ]
                    }}
                />
            </Source>

        </>

    );
};

export default TrafficDensityLayer;