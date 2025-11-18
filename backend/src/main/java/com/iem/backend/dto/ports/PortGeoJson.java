package com.iem.backend.dto.ports;

import java.util.Map;

public record PortGeoJson(
        String type,
        Map<String, Object> properties,
        Map<String, Object> geometry
) {
}
