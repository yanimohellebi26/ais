package com.iem.backend.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.iem.backend.dto.analytics.AnalyticsFilter;
import com.iem.backend.entity.CustomUserDetails;
import com.iem.backend.service.PortRouteService;

@RestController
@RequestMapping("/api/v1/trajectories")
public class TrajectoriesController {

    private final PortRouteService portRouteService;

    public TrajectoriesController(PortRouteService portRouteService) {
        this.portRouteService = portRouteService;
    }

    @GetMapping("/port-routes")
    public ResponseEntity<String> getPortRoutes(
        @RequestParam double minLat,
        @RequestParam double maxLat,
        @RequestParam double minLon,
        @RequestParam double maxLon,
        @RequestParam int zoom,
        @ModelAttribute AnalyticsFilter filters,
        @AuthenticationPrincipal CustomUserDetails currentUser
    ) {
        String geoJson = portRouteService.getRoutesAsFeatureCollection(currentUser, filters, minLat, maxLat, minLon, maxLon, zoom);
        return ResponseEntity.ok()
            .header("Content-Type", "application/json")
            .body(geoJson);
    }
    
}
