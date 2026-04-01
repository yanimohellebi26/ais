import TrafficDensityLayer from "../layers/TrafficDensityLayer";
import React from "react";
import { Map } from "@vis.gl/react-maplibre";
import {MAP_STYLES, DEFAULT_VIEW_STATE_PREVIEW} from "../constants/mapStyles";
import { AnalyticsFilters } from "../../Analytics/Components/interfaces";

interface Props {
    gridSize?: number;
    filters?: AnalyticsFilters;
    width?: number | string;
    height?: number | string;
}

const TrafficDensityWidget: React.FC<Props> = ({ gridSize = 0.1, filters, width = "100%", height = 150 }) => {

    return (
        <div style={{ width, height, borderRadius: "0.5rem", overflow: "hidden" }}>
            <Map
                initialViewState={DEFAULT_VIEW_STATE_PREVIEW}
                mapStyle={MAP_STYLES.STANDARD}
                interactive={false}
                style={{ width: "100%", height: "100%" }}
            >
                <TrafficDensityLayer gridSize={gridSize} filters={filters} />
            </Map>
        </div>
    );
};

export default TrafficDensityWidget;