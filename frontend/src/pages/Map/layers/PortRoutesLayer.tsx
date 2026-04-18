import React, { useState } from "react";
import { Source, Layer, Popup } from "@vis.gl/react-maplibre";
import { usePortRoutes } from "../../../hooks/usePortRoutes";

const PortRoutesLayer: React.FC<{ filters?: any }> = ({ filters }) => {
    const { data, loading } = usePortRoutes({ filters });
    const [hoverInfo, setHoverInfo] = useState<any>(null);

    return (
        <>
            <Source id="port-routes-data" type="geojson" data={data}>
                <Layer
                    id="port-routes-line"
                    type="line"
                    paint={{
                        'line-color': '#3498db',
                        'line-width': ['interpolate', ['linear'], ['get', 'count'], 1, 1.5, 20, 6],
                        'line-opacity': 0.8
                    }}
                    interactive={true}
                    onMouseMove={e => {
                        if (e.features?.length) {
                            setHoverInfo({
                                lngLat: e.lngLat,
                                props: e.features[0].properties
                            });
                        }
                    }}
                    onMouseLeave={() => setHoverInfo(null)}
                />
            </Source>

            {hoverInfo && (
                <Popup longitude={hoverInfo.lngLat.lng} latitude={hoverInfo.lngLat.lat} closeButton={false}>
                    <div className="p-1 text-xs">
                        <div className="font-bold border-bottom mb-1">{hoverInfo.props.srcPort} ➔ {hoverInfo.props.destPort}</div>
                        <div>🚢 <b>{hoverInfo.props.count}</b> navires</div>
                        <div>⏱️ <b>{Math.round(hoverInfo.props.avgDuration)}</b> min moy.</div>
                    </div>
                </Popup>
            )}
        </>
    );
};

export default PortRoutesLayer;