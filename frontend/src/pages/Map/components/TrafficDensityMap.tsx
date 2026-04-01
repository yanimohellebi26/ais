import React, {  useState } from "react";
import { Map } from "@vis.gl/react-maplibre";
import TrafficDensityLayer from "../layers/TrafficDensityLayer";
import {MAP_STYLES, MAP_CONFIG, DEFAULT_VIEW_STATE} from "../constants/mapStyles";
import MapFilterDrawer from "./MapFilterDrawer";
import {AnalyticsFilters} from "../../Analytics/Components/interfaces";


interface Props {
    filters?: AnalyticsFilters;
    gridSize?: number;
}

const TrafficDensityMap: React.FC<Props> = ({ filters }) => {

    const [gridSize, setGridSize] = useState<number>(0.1);

    return (
        <div className="h-[90vh] w-full rounded-2xl shadow-sm overflow-hidden">
            <MapFilterDrawer>
                <div className="form-control w-full mt-4">
                    <label className="label">
                        <span className="label-text font-medium">Grid Size (°)</span>
                    </label>
                    <input
                        type="range"
                        min={0.1}
                        max={2}
                        step={0.1}
                        value={gridSize}
                        className="range range-primary range-sm"
                        onChange={(e) => setGridSize(Number(e.target.value))}
                    />
                    <div className="text-xs mt-1 text-gray-500 text-right">
                        Current value: <span className="font-semibold">{gridSize.toFixed(2)}°</span>
                    </div>
                </div>
            </MapFilterDrawer>
            <Map
                initialViewState={DEFAULT_VIEW_STATE}
                mapStyle={MAP_STYLES.STANDARD}
                minZoom={MAP_CONFIG.MIN_ZOOM}
                maxZoom={MAP_CONFIG.MAX_ZOOM}
                style={{ width: "100%", height: "100%" }}
            >
                <TrafficDensityLayer filters={filters} gridSize={gridSize} />
            </Map>
        </div>
    );
};

export default TrafficDensityMap;