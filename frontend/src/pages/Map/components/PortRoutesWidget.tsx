import React from "react";
import { Map } from "@vis.gl/react-maplibre";
import { MAP_STYLES, DEFAULT_VIEW_STATE_PREVIEW } from "../constants/mapStyles";
import { AnalyticsFilters } from "../../Analytics/Components/interfaces";
import PortRoutesLayer from "../layers/PortRoutesLayer";

interface Props {
    filters?: AnalyticsFilters;
    width?: number | string;
    height?: number | string;
}

const PortRoutesWidget: React.FC<Props> = ({ filters, width = "100%", height = 150 }) => {
    return (
        <div style={{ width, height, borderRadius: "0.5rem", overflow: "hidden" }} className="border border-base-200">
            <Map
                initialViewState={DEFAULT_VIEW_STATE_PREVIEW}
                mapStyle={MAP_STYLES.STANDARD}
                interactive={false}
                style={{ width: "100%", height: "100%" }}
            >
                <PortRoutesLayer filters={filters} />
            </Map>
        </div>
    );
};

export default PortRoutesWidget;