package com.iem.backend.common.geoJson;


import org.locationtech.jts.geom.Point;
import org.springframework.stereotype.Component;

@Component
public class GeoJsonMapper {

    public GeoJsonGeometry point(Point point) {
        return new GeoJsonGeometry(
                "Point",
                new double[]{point.getX(), point.getY()}
        );
    }

    public <T> GeoJsonFeature<T> feature(T props, GeoJsonGeometry geometry) {
        return new GeoJsonFeature<>(props, geometry);
    }

    public <T> GeoJsonFeatureCollection<T> featureCollection(
            java.util.List<GeoJsonFeature<T>> features
    ) {
        return new GeoJsonFeatureCollection<>(features);
    }
}

