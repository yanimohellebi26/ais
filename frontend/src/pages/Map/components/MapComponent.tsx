import React, { useRef } from "react";
import { Map as MapIcon, Globe, Maximize, Minimize, Anchor } from "lucide-react";
import { Map } from "@vis.gl/react-maplibre";
import "maplibre-gl/dist/maplibre-gl.css";
import VesselLayer from "../layers/VesselLayer";
import MapFilterDrawer from "./MapFilterDrawer";
import PortLayer from "../layers/PortLayer";
import SelectedVesselPanel from "../filters/SelectedVesselPanel";
import { useMapFilters } from "../hooks/useMapFilters";
import {MAP_STYLES, DEFAULT_VIEW_STATE, MAP_CONFIG} from "../constants/mapStyles";
import Breadcrumbs from "../../../components/BaseComponents/Breadcrumbs";
import ToggleButton from "../../../components/BaseComponents/ToggleButton";
import DatePicker from "../../../components/BaseComponents/DatePicker";
import Slider from "../../../components/BaseComponents/Slider";
import {DateRange} from "react-day-picker";

const mapStyles = Object.values(MAP_STYLES);

const MapComponent: React.FC = () => {
    const {
        styleIndex,
        limit,
        isFullscreen,
        selectedRange,
        showPorts,
        selectedVesselId,
        selectedPositionId,
        targetDate,
        targetRadiusKm,
        setStyleIndex,
        setLimit,
        setIsFullscreen,
        setSelectedRange,
        setShowPorts,
        handleVesselClick,
        handleUpdateFilters,
        handleReset
    } = useMapFilters();

    const mapContainerRef = useRef<HTMLDivElement>(null);

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
            <h1 className="text-2xl font-semibold mr-4 pb-4" >Interactive Sea Sight Map</h1>

            <MapFilterDrawer>
                {selectedVesselId && (
                    <SelectedVesselPanel
                        vesselId={selectedVesselId}
                        initialDate={targetDate}
                        initialRadiusKm={targetRadiusKm}
                        onSearch={handleUpdateFilters}
                        onReset={handleReset}
                    />
                )}

                <div className="flex items-center gap-4">
                    <ToggleButton
                        onIcon={<Anchor className="text-success" />}
                        offIcon={<Anchor className="text-error" />}
                        onToggle={() => setShowPorts((prev) => !prev)}
                        isOn={showPorts}
                    />
                    <span className="text-base-content/80">Toggle ports</span>
                </div>

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
                    onSelect={(value) => setSelectedRange(value as DateRange | undefined)}
                />
            </MapFilterDrawer>

            <div className="flex gap-4 h-[80vh]">
                <div
                    ref={mapContainerRef}
                    className="flex-1 relative rounded-2xl shadow-sm bg-base-100 border-accent overflow-hidden"
                >
                    <Map
                        initialViewState={DEFAULT_VIEW_STATE}
                        style={{ width: "100%", height: "100%" }}
                        minZoom={MAP_CONFIG.MIN_ZOOM}
                        maxZoom={MAP_CONFIG.MAX_ZOOM}
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
                                targetVesselId={selectedVesselId ?? undefined}
                                targetPositionId={selectedPositionId ?? undefined}
                                targetDate={targetDate}
                                targetRadiusKm={targetRadiusKm}
                                onVesselClick={handleVesselClick}
                            />
                            {showPorts && <PortLayer />}
                        </div>
                    </Map>
                </div>
            </div>
        </>
    );
};

export default MapComponent;