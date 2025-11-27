package com.iem.backend.common.geoJson;

import java.util.List;

public record GeoJsonFeatureCollection<T>(
        String type,
        List<GeoJsonFeature<T>> features
) {
    public GeoJsonFeatureCollection(List<GeoJsonFeature<T>> features) {
        this("FeatureCollection", features);
    }
}

