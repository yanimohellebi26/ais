import React from "react";
import { Source, Layer, useMap } from "@vis.gl/react-maplibre";
import { useTrafficDensity } from "../../../hooks/useTrafficDensity";
import { DateRange } from "react-day-picker";
import { useMapHover } from "../hooks/useMapHover";
import { useCallback } from "react";
import TrafficDensityTooltip from "../tooltips/TrafficDensityTooltip";

interface Props {
    dateRange?: DateRange;
    gridSize?: number;
}

const TrafficDensityLayer: React.FC<Props> = ({ dateRange, gridSize }) => {
    const { current: map } = useMap();
    if (!map) return null;
    const { geoJson, stats } = useTrafficDensity({ map, gridSize, dateRange });

    const { tooltipData } = useMapHover<any>(
        map,
        "traffic-points",
        "traffic-density",
        useCallback((props: any) => ({
            density: props.density,
            lat: props.lat,
            lon: props.lon
        }), [])
    );

    if (!geoJson || !stats || geoJson.features.length == 0) return null;

    const normalizedDensity: any = [
        "/",
        [
            "-",
            [
                "max",
                stats.min,
                ["min", ["get", "density"], stats.max]
            ],
            stats.min
        ],
        Math.max(1, stats.max - stats.min)
    ];

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
                            normalizedDensity,
                            0, 0,
                            1, 1
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
                                normalizedDensity,
                                0, 2,
                                0.5, 10,
                                1, 30
                            ],
                            16,
                            [
                                "interpolate",
                                ["linear"],
                                normalizedDensity,
                                0, 5,
                                0.5, 20,
                                1, 50
                            ]
                        ],
                        "circle-color": [
                            "interpolate",
                            ["linear"],
                            normalizedDensity,
                            0, "rgba(33,102,172,0)",
                            0.2, "rgb(103,169,207)",
                            0.4, "rgb(209,229,240)",
                            0.6, "rgb(253,219,199)",
                            0.8, "rgb(239,138,98)",
                            1, "rgb(178,24,43)"
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

            {tooltipData && (
                <TrafficDensityTooltip
                    data={tooltipData.data}
                    x={tooltipData.x}
                    y={tooltipData.y}
                />
            )}

        </>

    );
};

export default TrafficDensityLayer;