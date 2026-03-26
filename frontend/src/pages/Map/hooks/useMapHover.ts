import { useState, useRef, useCallback, useEffect } from "react";
import { MapRef } from "@vis.gl/react-maplibre";

export const useMapHover = <T>(
    mapRef: MapRef | undefined,
    layerId: string,
    sourceId: string,
    parseFeature: (properties: any) => T
) => {
    const hoverRef = useRef<number | string | null>(null);
    const [tooltipData, setTooltipData] = useState<{
        data: T;
        x: number;
        y: number;
    } | null>(null);

    const handleMouseMove = useCallback((e: any) => {
        const map = mapRef?.getMap();
        if (!map) return;

        const features = map.queryRenderedFeatures(e.point, { layers: [layerId] });
        const previousHoverId = hoverRef.current;

        if (features.length > 0) {
            const feature = features[0];
            const featureId = feature.id ?? null;

            if (featureId !== previousHoverId) {
                // Remove old hover
                if (previousHoverId !== null) {
                    map.setFeatureState(
                        { source: sourceId, id: previousHoverId },
                        { hover: false }
                    );
                }

                // Add new hover
                if (featureId !== null) {
                    map.setFeatureState(
                        { source: sourceId, id: featureId },
                        { hover: true }
                    );
                }

                hoverRef.current = featureId;

                const canvas = map.getCanvas();
                const rect = canvas.getBoundingClientRect();

                // Update tooltip
                setTooltipData({
                    data: parseFeature(feature.properties),
                    x: rect.left + e.point.x,
                    y: rect.top + e.point.y
                });
            } else {
                // Update position only
                const canvas = map.getCanvas();
                const rect = canvas.getBoundingClientRect();

                setTooltipData((prev) => prev ? {
                    ...prev,
                    x: rect.left + e.point.x,
                    y: rect.top + e.point.y
                } : null);
            }
        } else {
            // Clear hover & tooltip
            if (previousHoverId !== null) {
                map.setFeatureState(
                    { source: sourceId, id: previousHoverId },
                    { hover: false }
                );
                hoverRef.current = null;
            }
            setTooltipData(null);
        }
    }, [mapRef, layerId, sourceId, parseFeature]);

    useEffect(() => {
        const map = mapRef?.getMap();
        if (!map) return;

        const onEnter = () => {
            map.getCanvas().style.cursor = "pointer";
        };

        const onLeave = () => {
            map.getCanvas().style.cursor = "";
            if (hoverRef.current !== null) {
                map.setFeatureState(
                    { source: sourceId, id: hoverRef.current },
                    { hover: false }
                );
                hoverRef.current = null;
            }
            setTooltipData(null);
        };

        map.on("mouseenter" as any, layerId, onEnter);
        map.on("mouseleave" as any, layerId, onLeave);
        map.on("mousemove" as any, layerId, handleMouseMove);

        return () => {
            map.off("mouseenter" as any, layerId, onEnter);
            map.off("mouseleave" as any, layerId, onLeave);
            map.off("mousemove" as any, layerId, handleMouseMove);
        };
    }, [mapRef, layerId, sourceId, handleMouseMove]);

    return { tooltipData, hoverRef };
};