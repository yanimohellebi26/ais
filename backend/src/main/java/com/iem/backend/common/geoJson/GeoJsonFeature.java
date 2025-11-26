package com.iem.backend.common.geoJson;

public record GeoJsonFeature<T>(
        String type,
        Object id,
        T properties,
        GeoJsonGeometry geometry
) {
    public GeoJsonFeature(Object id, T properties, GeoJsonGeometry geometry) {
        this("Feature", id, properties, geometry);
    }
}

