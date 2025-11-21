package com.iem.backend.common.geoJson;

public record GeoJsonGeometry(
        String type,
        Object coordinates
) {}

