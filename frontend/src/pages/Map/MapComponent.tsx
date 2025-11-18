import React, { useState, useRef } from "react";
import TitleH1 from "../../components/BaseComponents/TitleH1";
import ToggleButton from "../../components/BaseComponents/ToggleButton";
import Breadcrumbs from "../../components/BaseComponents/Breadcrumbs";
import Slider from "../../components/BaseComponents/Slider";
import { Map as MapIcon, Globe, Maximize, Minimize } from "lucide-react";
import { Map } from "@vis.gl/react-maplibre";
import "maplibre-gl/dist/maplibre-gl.css";
import VesselLayer from "./MapLayers/VesselLayer";
import MapFilterDrawer from "./MapFilterDrawer";
import DatePicker from "../../components/BaseComponents/DatePicker";
import { DateRange } from "react-day-picker";

const mapStyles = [
    "https://demotiles.maplibre.org/globe.json",
    "https://demotiles.maplibre.org/style.json",
];

const MapComponent: React.FC = () => {
    const [styleIndex, setStyleIndex] = useState(0);
    const [limit, setLimit] = useState(500);
    const [isFullscreen, setIsFullscreen] = useState(false);
    const [selectedRange, setSelectedRange] = useState<DateRange | undefined>(undefined);

    const [selectedVesselMmsi, setSelectedVesselMmsi] = useState<string | null>(null);
    const [targetDate, setTargetDate] = useState<string | undefined>();
    const [targetRadiusKm, setTargetRadiusKm] = useState<number | undefined>();

    const mapContainerRef = useRef<HTMLDivElement>(null);

    const handleVesselClick = (mmsi: string) => {
        setSelectedVesselMmsi(mmsi);
        setTargetDate(undefined);
        setTargetRadiusKm(undefined);
    };

    const handleUpdateFilters = (date?: string, radiusKm?: number) => {
        setTargetDate(date);
        setTargetRadiusKm(radiusKm);
    };

    const handleReset = () => {
        setSelectedVesselMmsi(null);
        setTargetDate(undefined);
        setTargetRadiusKm(undefined);
    };

    const switchMapStyle = () => {
        setStyleIndex((prev) => (prev + 1) % mapStyles.length);
    };

    const toggleFullscreen = () => {
        if (!mapContainerRef.current) return;

        if (!isFullscreen) {
            mapContainerRef.current.requestFullscreen?.();
        } else {
            document.exitFullscreen?.();
        }
        setIsFullscreen(!isFullscreen);
    };

    return (
        <>
            <Breadcrumbs />
            <TitleH1>Interactive Sea Sight Map</TitleH1>
            <MapFilterDrawer
                selectedVesselMmsi={selectedVesselMmsi ?? undefined}
                targetDate={targetDate}
                targetRadiusKm={targetRadiusKm}
                onFetchNearbyVessels={handleUpdateFilters}
                resetSelectedVessel={handleReset}
            >
                <Slider
                    label="Limit Positions"
                    min={400}
                    max={2000}
                    step={400}
                    value={limit}
                    onChange={setLimit}
                />

                <DatePicker
                    mode="range"
                    selected={selectedRange}
                    onSelect={(value) => {
                        setSelectedRange(value as DateRange | undefined);
                    }}
                />
            </MapFilterDrawer>

            <div className="flex gap-4 h-[80vh]">
                <div
                    ref={mapContainerRef}
                    className="flex-1 relative rounded-2xl shadow-sm bg-base-100 border-accent overflow-hidden"
                >
                    <Map
                        initialViewState={{
                            longitude: -100,
                            latitude: 36,
                            zoom: 2.5,
                        }}
                        style={{ width: "100%", height: "100%" }}
                        mapStyle={mapStyles[styleIndex]}
                    >
                        <div className="flex flex-col p-4 gap-4">
                            <ToggleButton
                                onIcon={<MapIcon />}
                                offIcon={<Globe />}
                                onToggle={switchMapStyle}
                            />
                            <ToggleButton
                                onIcon={<Minimize size={20} />}
                                offIcon={<Maximize size={20} />}
                                onToggle={toggleFullscreen}
                            />
                            <VesselLayer
                                limit={limit}
                                dateRange={selectedRange}
                                targetMmsi={selectedVesselMmsi ?? undefined}
                                targetDate={targetDate}
                                targetRadiusKm={targetRadiusKm}
                                onVesselClick={handleVesselClick}
                            />
                        </div>
                    </Map>
                </div>
            </div>
        </>
    );
};

export default MapComponent;
