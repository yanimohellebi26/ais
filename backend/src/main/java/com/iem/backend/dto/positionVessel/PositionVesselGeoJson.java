package com.iem.backend.dto.positionVessel;

import java.util.Map;

public record PositionVesselGeoJson(
        String type,
        Map<String, Object> properties,
        Map<String, Object> geometry
) {
}
