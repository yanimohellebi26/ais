package com.iem.backend.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
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

    @PostMapping("/port-routes")
    public ResponseEntity<String> getPortRoutes(
        @RequestBody AnalyticsFilter filters,
        @AuthenticationPrincipal CustomUserDetails currentUser
    ) {
        String geoJson = portRouteService.getRoutesAsFeatureCollection(currentUser, filters);
        return ResponseEntity.ok()
            .header("Content-Type", "application/json")
            .body(geoJson);
    }
    
}
