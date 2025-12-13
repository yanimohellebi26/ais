import React, { useEffect, useMemo, useCallback } from "react";
import { Source, Layer, useMap } from "@vis.gl/react-maplibre";
import { useVesselPositions } from "../../../hooks/useVesselPositions";
import { useVesselPositionsRadius } from "../../../hooks/useVesselPositionsRadius";
import { DateRange } from "react-day-picker";
import VesselTooltip from "../tooltips/VesselTooltip";
import { VesselGeoJson } from "../types/map";
import { useMapHover } from "../hooks/useMapHover";
import { createRadiusCircle } from "../utils/mapGeometry";
import { CLUSTER_CONFIG, VESSEL_COLORS } from "../constants/mapStyles";

interface Props {
    limit?: number;
    dateRange?: DateRange;
    targetVesselId?: number;
    targetPositionId?: number;
    targetDate?: string;
    targetRadiusKm?: number;
    onVesselClick?: (vesselId: number, positionId: number) => void;
    ids?: number[];
}

const VesselLayer: React.FC<Props> = ({
                                          limit,
                                          dateRange,
                                          targetVesselId,
                                          targetPositionId,
                                          targetDate,
                                          targetRadiusKm,
                                          onVesselClick,
                                          ids
                                      }) => {
    const { current: map } = useMap();

    const radiusGeoJson = useVesselPositionsRadius({
        map,
        vesselId: targetVesselId ?? -1,
        date: targetDate,
        radiusKm: targetRadiusKm,
        enabled: targetVesselId != null
    });

    const normalGeoJson = useVesselPositions({
        map,
        limit,
        dateRange,
        ids
    });

    const isRadiusMode = targetVesselId != null;
    const geoJson = isRadiusMode ? radiusGeoJson : normalGeoJson;
    const clusterMaxZoom = isRadiusMode ? CLUSTER_CONFIG.MAX_ZOOM_RADIUS : CLUSTER_CONFIG.MAX_ZOOM_NORMAL;

    // Parse feature for hover
    const parseVesselFeature = useCallback((props: any): VesselGeoJson => ({
        vesselId: props.vesselId,
        vesselName: props.vesselName,
        mmsi: props.mmsi,
        sog: props.sog,
        cog: props.cog,
        heading: props.heading,
        status: props.status,
        baseDateTime: props.baseDateTime,
        distanceKm: props.distanceKm
    }), []);

    // Use hover hook
    const { tooltipData } = useMapHover<VesselGeoJson>(
        map,
        "unclustered-point",
        "vessels-source",
        parseVesselFeature
    );

    // GeoJson circle radius
    const radiusCircleGeoJson = useMemo(() => {
        if (!isRadiusMode || !targetRadiusKm || !radiusGeoJson?.features?.length) {
            return null;
        }

        const targetFeature = radiusGeoJson.features.find(
            (f: any) => f.properties.id === targetPositionId
        );

        if (!targetFeature) return null;

        const [lng, lat] = targetFeature.geometry.coordinates;
        return createRadiusCircle(lng, lat, targetRadiusKm);
    }, [isRadiusMode, targetRadiusKm, targetPositionId, radiusGeoJson]);

    // Click handler
    const handleClick = useCallback((e: any) => {
        if (!map) return;
        const features = map.queryRenderedFeatures(e.point, {
            layers: ["unclustered-point"]
        });
        if (features.length === 0) return;

        const vesselId = features[0].properties?.vesselId;
        const positionId = features[0].properties?.id;

        if (targetRadiusKm != null && vesselId === targetVesselId) {
            return;
        }
        
        if (vesselId != null) onVesselClick?.(Number(vesselId), Number(positionId));
    }, [map, onVesselClick, targetRadiusKm, targetVesselId]);

    useEffect(() => {
        if (!map) return;
        map.on("click", handleClick);
        return () => {
            map.off("click", handleClick);
        };
    }, [map, handleClick]);

    if (!geoJson) return null;

    return (
        <>
            {radiusCircleGeoJson && (
                <Source
                    id="radius-circle-source"
                    type="geojson"
                    data={radiusCircleGeoJson}
                >
                    <Layer
                        id="radius-circle-fill"
                        type="fill"
                        paint={{
                            "fill-color": VESSEL_COLORS.RADIUS_CIRCLE,
                            "fill-opacity": 0.1
                        }}
                    />
                    <Layer
                        id="radius-circle-outline"
                        type="line"
                        paint={{
                            "line-color": VESSEL_COLORS.RADIUS_CIRCLE,
                            "line-width": 2,
                            "line-opacity": 0.5,
                            "line-dasharray": [2, 2]
                        }}
                    />
                </Source>
            )}

            <Source
                key={isRadiusMode ? "radius" : "normal"}
                id="vessels-source"
                type="geojson"
                data={geoJson}
                cluster={true}
                clusterRadius={CLUSTER_CONFIG.RADIUS}
                clusterMaxZoom={clusterMaxZoom}
            >
                <Layer
                    id="clusters"
                    type="circle"
                    filter={["has", "point_count"]}
                    paint={{
                        "circle-color": [
                            "step",
                            ["get", "point_count"],
                            "#51bbd6", 10,
                            "#3b84aa", 30,
                            "#032f53",
                        ],
                        "circle-radius": ["step", ["get", "point_count"], 15, 10, 20, 30, 25],
                    }}
                />

                <Layer
                    id="cluster-count"
                    type="symbol"
                    filter={["has", "point_count"]}
                    layout={{
                        "text-field": "{point_count_abbreviated}",
                        "text-font": ["Open Sans Bold"],
                        "text-size": 12
                    }}
                    paint={{
                        "text-color": "#ffffff",
                    }}
                />

                <Layer
                    id="unclustered-point"
                    type="circle"
                    filter={["!", ["has", "point_count"]]}
                    paint={{
                        "circle-radius": [
                            "case",
                            ["boolean", ["feature-state", "hover"], false],
                            10,
                            6
                        ],
                        "circle-color": [
                            "case",
                            ["==", ["get", "id"], targetPositionId ?? -1],
                            VESSEL_COLORS.CLICKED_POSITION,
                            ["==", ["get", "vesselId"], targetVesselId ?? -1],
                            VESSEL_COLORS.SELECTED,
                            VESSEL_COLORS.NORMAL
                        ],
                        "circle-stroke-width": 2,
                        "circle-stroke-color": "#FFFFFF",
                    }}
                />
            </Source>

            {tooltipData && (
                <VesselTooltip
                    data={tooltipData.data}
                    x={tooltipData.x}
                    y={tooltipData.y}
                />
            )}
        </>
    );
};

export default VesselLayer;