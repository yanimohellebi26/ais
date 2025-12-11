package com.iem.backend.service;

import com.iem.backend.common.geoJson.GeoJsonFeature;
import com.iem.backend.common.geoJson.GeoJsonFeatureCollection;
import com.iem.backend.common.geoJson.GeoJsonGeometry;
import com.iem.backend.common.geoJson.GeoJsonMapper;
import org.springframework.stereotype.Service;
import org.locationtech.jts.geom.Point;

import java.util.List;
import java.util.function.Function;

@Service
public class GeoJsonService {

    private final GeoJsonMapper geoJsonMapper;

    public GeoJsonService(GeoJsonMapper geoJsonMapper) {
        this.geoJsonMapper = geoJsonMapper;
    }

    /**
     * Generate a FeatureCollection generic for any entity
     *
     * @param entities   entity list
     * @param toProps    function to map entity to dto properties
     * @param toGeometry function to get Point geometry of entity
     * @param <E>        entity type
     * @param <T>        properties type (DTO)
     * @return FeatureCollection generic
     */
    public <E, T> GeoJsonFeatureCollection<T> toGeoJson(
            List<E> entities,
            Function<E, Object> getId,
            Function<E, T> toProps,
            Function<E, Point> toGeometry
    ) {

        List<GeoJsonFeature<T>> features = entities.stream()
                .map(entity -> {
                    T props = toProps.apply(entity);
                    GeoJsonGeometry geom = geoJsonMapper.point(toGeometry.apply(entity));
                    Object id = getId.apply(entity);
                    return geoJsonMapper.feature(id, props, geom);
                })
                .toList();

        return geoJsonMapper.featureCollection(features);
    }

}
