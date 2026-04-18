import React from "react";
import { Map } from "@vis.gl/react-maplibre";
import { MAP_STYLES, MAP_CONFIG, DEFAULT_VIEW_STATE } from "../constants/mapStyles";
import MapFilterDrawer from "./MapFilterDrawer";
import { AnalyticsFilters } from "../../Analytics/Components/interfaces";
import PortRoutesLayer from "../layers/PortRoutesLayer";
import "maplibre-gl/dist/maplibre-gl.css"; 

interface Props {
    filters?: AnalyticsFilters;
}

const PortRoutesMap: React.FC<Props> = ({ filters }) => {
    return (
        <div className="h-[90vh] w-full rounded-2xl shadow-sm overflow-hidden relative bg-base-100">
            <div className="absolute inset-0 z-10 pointer-events-none">
                <div className="pointer-events-auto inline-block">
                    <MapFilterDrawer title="Routes Analysis">
                        <div className="mt-4">
                            <p className="text-sm text-gray-500 italic">
                                The thickness of the lines represents the traffic volume. 
                                Hover over a route to see details.
                            </p>
                        </div>
                    </MapFilterDrawer>
                </div>
            </div>

            <Map
                initialViewState={DEFAULT_VIEW_STATE}
                mapStyle={MAP_STYLES.STANDARD}
                minZoom={MAP_CONFIG.MIN_ZOOM}
                maxZoom={MAP_CONFIG.MAX_ZOOM}
                style={{ width: "100%", height: "100%" }}
            >
                <PortRoutesLayer filters={filters} />
            </Map>
        </div>
    );
};

export default PortRoutesMap;