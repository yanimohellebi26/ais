import TrafficDensityLayer from "../layers/TrafficDensityLayer";
import React, {  useState } from "react";
import { Map } from "@vis.gl/react-maplibre";
import {MAP_STYLES, DEFAULT_VIEW_STATE_PREVIEW} from "../constants/mapStyles";
import {DateRange} from "react-day-picker";

interface Props {
    gridSize?: number;
    dateRange?: DateRange;
    width?: number | string;
    height?: number | string;
}

const TrafficDensityWidget: React.FC<Props> = ({ gridSize = 0.1, dateRange, width = "100%", height = 150 }) => {
    const [mapRef, setMapRef] = useState<any>(null);

    return (
        <div style={{ width, height, borderRadius: "0.5rem", overflow: "hidden" }}>
            <Map
                initialViewState={DEFAULT_VIEW_STATE_PREVIEW}
                mapStyle={MAP_STYLES.STANDARD}
                interactive={false}
                style={{ width: "100%", height: "100%" }}
                ref={setMapRef}
            >
                {mapRef && <TrafficDensityLayer gridSize={gridSize} dateRange={dateRange} />}
            </Map>
        </div>
    );
};

export default TrafficDensityWidget;