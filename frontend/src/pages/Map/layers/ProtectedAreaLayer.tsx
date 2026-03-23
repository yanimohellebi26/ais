import React, { useCallback } from "react";
import { Source, Layer, useMap } from "@vis.gl/react-maplibre";
import { useProtectedArea } from "../../../hooks/useProtectedArea";
import { useMapHover } from "../hooks/useMapHover";
import ProtectedAreaTooltip from "../tooltips/ProtectedAreaTooltip";

const IUCN_COLOR_MAP: Record<string, string> = {
    'Ia':             '#8B0000',
    'Ib':             '#B22222',
    'II':             '#D32F2F',
    'III':            '#FF4500',
    'IV':             '#FF9800',
    'V':              '#87CEEB',
    'VI':             '#000080',
    'Not Applicable': '#A9A9A9',
    'Not Assigned':   '#808080',
    'Not Reported':   '#D3D3D3',
};

const IUCN_COLORS = [
    'match', ['get', 'iucn_cat'],
    ...Object.entries(IUCN_COLOR_MAP).flat(),
    '#555555'
];

const getIucnColor = (iucn_cat: string) => IUCN_COLOR_MAP[iucn_cat] ?? '#555555';

const ProtectedAreaLayer: React.FC = () => {
    const { current: map } = useMap();
    const geoJson = useProtectedArea(map);

    const { tooltipData } = useMapHover<any>(
        map,
        "pa-fill",
        "pa-source",
        useCallback((props: any) => props, [])
    );

    const { tooltipData: pointTooltip } = useMapHover<any>(
        map,
        "pa-points",
        "pa-source",
        useCallback((props: any) => props, [])
    );

    if (!geoJson) return null;

    return (
        <>
            <Source id="pa-source" type="geojson" data={geoJson}>

                <Layer
                    id="pa-fill"
                    type="fill"
                    filter={['any', ['==', ['geometry-type'], 'Polygon'], ['==', ['geometry-type'], 'MultiPolygon']]}
                    paint={{
                        "fill-color": IUCN_COLORS,
                        "fill-opacity": ["case", ["boolean", ["feature-state", "hover"], false], 0.5, 0.3]
                    }}
                />

                <Layer
                    id="pa-outline"
                    type="line"
                    filter={['any', ['==', ['geometry-type'], 'Polygon'], ['==', ['geometry-type'], 'MultiPolygon']]}
                    paint={{
                        "line-color": IUCN_COLORS,
                        "line-width": 1,
                        "line-opacity": 0.8
                    }}
                />

                <Layer
                    id="pa-points"
                    type="circle"
                    filter={['==', ['geometry-type'], 'Point']}
                    paint={{
                        "circle-radius": 6,
                        "circle-color": IUCN_COLORS,
                        "circle-stroke-width": 1,
                        "circle-stroke-color": "#ffffff"
                    }}
                />
            </Source>

            {tooltipData && (
                <ProtectedAreaTooltip 
                    data={tooltipData.data} 
                    x={tooltipData.x} 
                    y={tooltipData.y}
                    placement="top"
                    color={getIucnColor(tooltipData.data.iucn_cat)}
                />
            )}

            {pointTooltip && (
                <ProtectedAreaTooltip 
                    data={pointTooltip.data} 
                    x={pointTooltip.x} 
                    y={pointTooltip.y} 
                    placement="bottom"
                    color={getIucnColor(pointTooltip.data.iucn_cat)}
                />
            )}
        </>
    );
};

export default ProtectedAreaLayer;