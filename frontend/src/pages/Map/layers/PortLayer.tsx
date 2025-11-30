import React, { useCallback } from "react";
import { Source, Layer, useMap } from "@vis.gl/react-maplibre";
import { usePortPositions } from "../../../hooks/usePortPositions";
import PortTooltip from "../tooltips/PortTooltip";
import { PortGeoJson } from "../types/map";
import { useMapHover } from "../hooks/useMapHover";
import { PORT_COLORS } from "../constants/mapStyles";

const PortLayer: React.FC = () => {
    const { current: map } = useMap();
    const geoJson = usePortPositions({ map });

    const shouldRender = !!geoJson;

    // Parse feature for hover
    const parsePortFeature = useCallback((props: any): PortGeoJson => ({
        portId: props.portId,
        name: props.name,
        code: props.code,
        country: props.country
    }), []);

    // Use hover hook
    const { tooltipData } = useMapHover<PortGeoJson>(
        map,
        "ports-symbol",
        "ports-source",
        parsePortFeature
    );

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
                            "circle-color": PORT_COLORS.NORMAL,
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

            {tooltipData && (
                <PortTooltip
                    data={tooltipData.data}
                    x={tooltipData.x}
                    y={tooltipData.y}
                />
            )}
        </>
    );
};

export default PortLayer;