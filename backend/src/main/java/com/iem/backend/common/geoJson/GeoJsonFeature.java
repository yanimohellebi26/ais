package com.iem.backend.common.geoJson;

public record GeoJsonFeature<T>(
        String type,
        T properties,
        GeoJsonGeometry geometry
) {
    public GeoJsonFeature(T properties, GeoJsonGeometry geometry) {
        this("Feature", properties, geometry);
    }
}
