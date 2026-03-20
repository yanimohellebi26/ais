package com.iem.backend.controller;

import com.iem.backend.common.geoJson.GeoJsonFeatureCollection;
import com.iem.backend.dto.analytics.TrafficDensity;
import com.iem.backend.entity.CustomUserDetails;
import com.iem.backend.service.GeoJsonService;
import com.iem.backend.service.TrafficDensityService;
import org.locationtech.jts.geom.Coordinate;
import org.locationtech.jts.geom.GeometryFactory;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

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
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate dateStart,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate dateEnd,
            @RequestParam(defaultValue = "0.1") double gridSize,
            @AuthenticationPrincipal CustomUserDetails currentUser
    ) {
        List<TrafficDensity> density = trafficDensityService.getTrafficDensity(
                currentUser,
                minLat, maxLat, minLon, maxLon,
                Optional.ofNullable(dateStart),
                Optional.ofNullable(dateEnd),
                gridSize
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