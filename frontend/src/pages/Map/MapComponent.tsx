import React, { useState } from "react";
import TitleH1 from "../../components/BaseComponents/TitleH1";
import ToggleButton from "../../components/BaseComponents/ToggleButton";
import Breadcrumbs from "../../components/BaseComponents/Breadcrumbs";
import { Map as MapIcon, Globe} from 'lucide-react'
import { Map } from '@vis.gl/react-maplibre';
import 'maplibre-gl/dist/maplibre-gl.css';
import VesselLayer from "../../components/MapLayers/VesselLayer";

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
            <ToggleButton onIcon={<MapIcon/>} offIcon={<Globe/>} onToggle={switchMapStyle}></ToggleButton>
            <div className="map-container">
                <Map
                    initialViewState={{
                    longitude: 3.49409153,
                    latitude: 47.94155256,
                    zoom: 3.5
                    }}
                    style={{width: '100%', height: '100%'}}
                    mapStyle={mapStyles[styleIndex]}
                > 
                <VesselLayer />
                </Map>
            </div>
            
        </div>
    );
};

export default MapComponent;