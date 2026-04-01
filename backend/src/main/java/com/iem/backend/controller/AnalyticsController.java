package com.iem.backend.controller;

import com.iem.backend.common.geoJson.GeoJsonFeatureCollection;
import com.iem.backend.dto.analytics.AnalyticsFilter;
import com.iem.backend.dto.analytics.TrafficDensity;
import com.iem.backend.entity.CustomUserDetails;
import com.iem.backend.service.GeoJsonService;
import com.iem.backend.service.TrafficDensityService;
import org.locationtech.jts.geom.Coordinate;
import org.locationtech.jts.geom.GeometryFactory;
import org.springdoc.core.annotations.ParameterObject;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/analytics")
public class AnalyticsController {

    private final TrafficDensityService trafficDensityService;
    private final GeoJsonService geoJsonService;

    private static final GeometryFactory GF = new GeometryFactory();

    public AnalyticsController(TrafficDensityService trafficDensityService, GeoJsonService geoJsonService) {
        this.trafficDensityService = trafficDensityService;
        this.geoJsonService = geoJsonService;
    }

    @GetMapping("/traffic-density")
    public ResponseEntity<GeoJsonFeatureCollection<TrafficDensity>> getTrafficDensity(
            @RequestParam double minLat,
            @RequestParam double maxLat,
            @RequestParam double minLon,
            @RequestParam double maxLon,
            @RequestParam(defaultValue = "0.1") double gridSize,
            @ModelAttribute @ParameterObject AnalyticsFilter filters,
            @AuthenticationPrincipal CustomUserDetails currentUser
    ) {
        List<TrafficDensity> density = trafficDensityService.getTrafficDensity(
                currentUser,
                minLat, maxLat, minLon, maxLon,
                gridSize,
                filters
        );

        if (density.isEmpty()) {
            return ResponseEntity.noContent().build();
        }

        return ResponseEntity.ok(geoJsonService.toGeoJson(
                density,
                td -> td.lat() + "-" + td.lon(),
                td -> td,
                td -> GF.createPoint(new Coordinate(td.lon(), td.lat()))
        ));
    }
}