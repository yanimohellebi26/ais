import React from "react";
import TitleH1 from "../../components/BaseComponents/TitleH1";
import Breadcrumbs from "../../components/BaseComponents/Breadcrumbs";
import MapComponent from "../../components/MapComponent"

const Map: React.FC = () => {
    return (
        <div>
            <Breadcrumbs />
            <TitleH1>Interactive Sea Sight Map</TitleH1>
            <MapComponent />
        </div>
    );
};

export default Map;