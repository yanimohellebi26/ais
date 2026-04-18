import React from "react";
import { Map } from "@vis.gl/react-maplibre";
import { MAP_STYLES, MAP_CONFIG, DEFAULT_VIEW_STATE } from "../constants/mapStyles";
import MapFilterDrawer from "./MapFilterDrawer";
import { AnalyticsFilters } from "../../Analytics/Components/interfaces";
import PortRoutesLayer from "../layers/PortRoutesLayer"; // Ton nouveau calque

interface Props {
    filters?: AnalyticsFilters;
}

const PortRoutesMap: React.FC<Props> = ({ filters }) => {
    return (
        <div className="h-[90vh] w-full rounded-2xl shadow-sm overflow-hidden relative">
            <MapFilterDrawer title="Routes Analysis">
                <div className="mt-4">
                    <p className="text-sm text-gray-500 italic">
                        The thickness of the lines represents the traffic volume between ports. 
                        Hover over a route to see details.
                    </p>
                </div>
            </MapFilterDrawer>

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