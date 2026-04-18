import React, { useCallback, useMemo } from "react";
import { Source, Layer, useMap } from "@vis.gl/react-maplibre";
import { usePortRoutes } from "../../../hooks/usePortRoutes";
import { useMapHover } from "../hooks/useMapHover";
import { PORT_COLORS } from "../constants/mapStyles";
import { Ship, Clock, ArrowRightLeft } from "lucide-react";

const PortRoutesLayer: React.FC<{ filters?: any }> = ({ filters }) => {
    const { current: map } = useMap();
    const { data: rawData } = usePortRoutes({ map, filters });

    const data = useMemo(() => {
        if (!rawData || !rawData.features) return rawData;
        return {
            ...rawData,
            features: rawData.features.map((f: any, index: number) => ({
                ...f,
                id: index + 1,
                properties: {
                    ...f.properties,
                    srcPort: f.properties.srcPort?.trim(),
                    destPort: f.properties.destPort?.trim()
                }
            }))
        };
    }, [rawData]);

    const portsGeoJson = useMemo(() => {
        if (!data || !data.features) return { type: "FeatureCollection", features: [] };
        const portMap = new Map();
        data.features.forEach((f: any) => {
            const coords = f.geometry.coordinates;
            const p = f.properties;
            if (coords && coords.length >= 2) {
                [{ n: p.srcPort, c: coords[0] }, { n: p.destPort, c: coords[coords.length - 1] }].forEach(pt => {
                    const cleanName = pt.n?.trim();
                    if (cleanName && !portMap.has(cleanName)) {
                        portMap.set(cleanName, {
                            type: "Feature",
                            geometry: { type: "Point", coordinates: pt.c },
                            properties: { name: cleanName }
                        });
                    }
                });
            }
        });
        return { type: "FeatureCollection", features: Array.from(portMap.values()) };
    }, [data]);

    const { tooltipData } = useMapHover<any>(
        map,
        "port-routes-line",
        "port-routes-source",
        useCallback((props: any) => props, [])
    );

    const hoveredSrc = tooltipData?.data?.srcPort || "";
    const hoveredDest = tooltipData?.data?.destPort || "";
    const isHovering = !!tooltipData;

    return (
        <>
            <Source id="port-routes-source" type="geojson" data={data}>
                <Layer
                    id="port-routes-line"
                    type="line"
                    paint={{
                        'line-color': ['case', ['boolean', ['feature-state', 'hover'], false], '#f39c12', '#2C12F3'],
                        'line-width': ['case', ['boolean', ['feature-state', 'hover'], false], 8, ['interpolate', ['linear'], ['get', 'count'], 1, 2, 20, 6]],
                        'line-opacity': ['case', ['boolean', ['feature-state', 'hover'], false], 1, isHovering ? 0.2 : 1.5]
                    }}
                />
            </Source>

            <Source id="ports-data-source" type="geojson" data={portsGeoJson}>
                <Layer
                    id="port-points"
                    type="circle"
                    paint={{
                        "circle-radius": ['case', ['any', ['==', ['get', 'name'], hoveredSrc], ['==', ['get', 'name'], hoveredDest]], 10, 5],
                        "circle-color": ['case', ['any', ['==', ['get', 'name'], hoveredSrc], ['==', ['get', 'name'], hoveredDest]], '#f39c12', PORT_COLORS.NORMAL],
                        "circle-stroke-width": 2,
                        "circle-stroke-color": "#ffffff",
                        "circle-opacity": ['case', !isHovering, 1, ['any', ['==', ['get', 'name'], hoveredSrc], ['==', ['get', 'name'], hoveredDest]], 1, 0.3]
                    }}
                />
                <Layer
                    id="port-labels"
                    type="symbol"
                    layout={{
                        'text-field': ['get', 'name'],
                        'text-size': ['case', ['any', ['==', ['get', 'name'], hoveredSrc], ['==', ['get', 'name'], hoveredDest]], 14, 10],
                        'text-anchor': 'top',
                        'text-offset': [0, 0.8]
                    }}
                    paint={{
                        'text-color': '#2c3e50',
                        'text-halo-color': '#ffffff',
                        'text-halo-width': 1.5,
                        'text-opacity': ['case', !isHovering, 1, ['any', ['==', ['get', 'name'], hoveredSrc], ['==', ['get', 'name'], hoveredDest]], 1, 0.1]
                    }}
                />
            </Source>

            {tooltipData && (
                <div 
                    className="fixed z-[9999] pointer-events-none bg-white rounded-lg shadow-2xl overflow-hidden border border-gray-100 font-sans min-w-[240px]"
                    style={{ 
                        left: tooltipData.x + 20, 
                        top: tooltipData.y - 20,
                        transform: 'translate(0, -50%)'
                    }}
                >
                    <div className="bg-gray-50 px-3 py-2 border-b border-gray-100 flex items-center gap-2">
                        <div className="bg-orange-100 p-1 rounded text-orange-600">
                            <ArrowRightLeft size={14} />
                        </div>
                        <div className="text-[13px] font-bold text-gray-800">
                            {tooltipData.data.srcPort} <span className="text-orange-500 mx-1">→</span> {tooltipData.data.destPort}
                        </div>
                    </div>

                    <div className="p-3 grid grid-cols-2 gap-3">
                        <div className="flex flex-col">
                            <div className="flex items-center gap-1 text-gray-400 text-[10px] uppercase font-bold">
                                <Ship size={12} className="text-blue-500" /> Traffic
                            </div>
                            <div className="text-base font-black text-gray-900">
                                {tooltipData.data.count} <span className="text-[10px] font-normal text-gray-400">Vessels</span>
                            </div>
                        </div>
                        <div className="flex flex-col">
                            <div className="flex items-center gap-1 text-gray-400 text-[10px] uppercase font-bold">
                                <Clock size={12} className="text-emerald-500" /> Avg. Time
                            </div>
                            <div className="text-base font-black text-gray-900">
                                {Math.round(tooltipData.data.avgDuration)} <span className="text-[10px] font-normal text-gray-400">Min</span>
                            </div>
                        </div>
                    </div>
                    
                    <div className="bg-orange-500 h-1 w-full" />
                </div>
            )}
        </>
    );
};

export default PortRoutesLayer;