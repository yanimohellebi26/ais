import React, { useEffect, useRef } from "react";
import { Source, Layer, useMap } from "@vis.gl/react-maplibre";
import { usePortPositions } from "../../../hooks/usePortPositions";

const PortLayer: React.FC = () => {
    const { current: map } = useMap();
    const geoJson = usePortPositions({ map });

    const shouldRender = !!geoJson;

    const hoverRef = useRef<number | string | null>(null);

    const tooltipRef = useRef<{ properties: any; x: number; y: number } | null>(null);
    const [, forceRender] = React.useState(0);

    const handleMouseMove = (e: maplibregl.MapMouseEvent) => {
        if (!map) return;

        const features = map.queryRenderedFeatures(e.point, { layers: ["ports-symbol"] });

        const previousHoverId = hoverRef.current;

        if (features.length > 0) {
            const feature = features[0];
            const featureId = feature.id ?? null;

            if (featureId !== previousHoverId) {
                if (previousHoverId !== null) {
                    map.setFeatureState(
                        { source: "ports-source", id: previousHoverId },
                        { hover: false }
                    );
                }

                if (featureId !== null) {
                    map.setFeatureState(
                        { source: "ports-source", id: featureId },
                        { hover: true }
                    );
                }

                hoverRef.current = featureId;

                tooltipRef.current = {
                    properties: feature.properties,
                    x: e.point.x,
                    y: e.point.y
                };
                forceRender(prev => prev + 1);
            } else {
                if (tooltipRef.current) {
                    tooltipRef.current.x = e.point.x;
                    tooltipRef.current.y = e.point.y;
                    forceRender(prev => prev + 1);
                }
            }
        } else {
            if (previousHoverId !== null) {
                map.setFeatureState(
                    { source: "ports-source", id: previousHoverId },
                    { hover: false }
                );
                hoverRef.current = null;
            }

            if (tooltipRef.current !== null) {
                tooltipRef.current = null;
                forceRender(prev => prev + 1);
            }
        }
    };

    useEffect(() => {
        if (!map) return;
        const layerId = "ports-symbol";

        const onMouseEnter = () => {
            map.getCanvas().style.cursor = "pointer";
        };
        const onMouseLeave = () => {
            map.getCanvas().style.cursor = "";
            if (hoverRef.current !== null) {
                map.setFeatureState(
                    { source: "ports-source", id: hoverRef.current },
                    { hover: false }
                );
                hoverRef.current = null;
            }
            tooltipRef.current = null;
            forceRender(prev => prev + 1);
        };

        map.on("mouseenter" as any, layerId, onMouseEnter);
        map.on("mouseleave" as any, layerId, onMouseLeave);
        map.on("mousemove" as any, layerId, handleMouseMove);

        return () => {
            map.off("mouseenter" as any, layerId, onMouseEnter);
            map.off("mouseleave" as any, layerId, onMouseLeave);
            map.off("mousemove" as any, layerId, handleMouseMove);
        };
    }, [map]);

    return (
        <>
            {shouldRender && (
                <Source id="ports-source" type="geojson" data={geoJson}>
                    <Layer
                        id="ports-symbol"
                        type="circle"
                        paint={{
                            "circle-radius": [
                                "case",
                                ["boolean", ["feature-state", "hover"], false],
                                14,
                                4
                            ],
                            "circle-color": "#b81b6f",
                            "circle-opacity": [
                                "case",
                                ["boolean", ["feature-state", "hover"], false],
                                1,
                                0.5
                            ]
                        }}
                    />
                </Source>
            )}

            {tooltipRef.current && (
                <div
                    style={{
                        position: "absolute",
                        left: tooltipRef.current.x + 10,
                        top: tooltipRef.current.y + 10,
                        background: "white",
                        padding: "5px 8px",
                        borderRadius: 4,
                        boxShadow: "0 1px 4px rgba(0,0,0,0.3)",
                        pointerEvents: "none",
                        fontSize: 12,
                    }}
                >
                    <div><strong>{tooltipRef.current.properties.name}</strong></div>
                    <div>Code: {tooltipRef.current.properties.code}</div>
                    <div>Country: {tooltipRef.current.properties.country}</div>
                </div>
            )}
        </>
    );
};

export default PortLayer;
