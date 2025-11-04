import React, { useState } from "react";
import TitleH1 from "../../components/BaseComponents/TitleH1";
import Button from "../../components/BaseComponents/Button";
import Breadcrumbs from "../../components/BaseComponents/Breadcrumbs";
import { Map } from '@vis.gl/react-maplibre';
import 'maplibre-gl/dist/maplibre-gl.css';

const mapStyles = [
    "https://demotiles.maplibre.org/globe.json",
    "https://demotiles.maplibre.org/style.json"
]

const MapComponent: React.FC = () => {
    const [styleIndex, setStyleIndex] = useState(0);

    const switchMapStyle = () => {
        setStyleIndex((prev) => (prev + 1) % mapStyles.length);
    };

    return (
        <div>
            <Breadcrumbs />
            <TitleH1>Interactive Sea Sight Map</TitleH1>
            <Button className="btn btn-sm" onClick={switchMapStyle}>Switch Map Style</Button>
            <div className="map-container">
                <Map
                    initialViewState={{
                    longitude: -100,
                    latitude: 40,
                    zoom: 3.5
                    }}
                    style={{width: '100%', height: '100%'}}
                    mapStyle={mapStyles[styleIndex]}
                />
            </div>
            
        </div>
    );
};

export default MapComponent;