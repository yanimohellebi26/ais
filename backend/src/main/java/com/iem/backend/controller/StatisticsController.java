package com.iem.backend.controller;

import com.iem.backend.dto.analytics.AnalyticsFilter;
import com.iem.backend.dto.statistics.VesselTypeStats;
import com.iem.backend.entity.CustomUserDetails;
import com.iem.backend.service.VesselTypeStatsService;
import org.springdoc.core.annotations.ParameterObject;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/statistics")
public class StatisticsController {

    private final VesselTypeStatsService vesselTypeStatsService;

    public StatisticsController(VesselTypeStatsService vesselTypeStatsService) {
        this.vesselTypeStatsService = vesselTypeStatsService;
    }

    @PostMapping("/vessel_type")
    public ResponseEntity<List<VesselTypeStats>> getVesselTypeStats(
            @RequestBody AnalyticsFilter filters,
            @AuthenticationPrincipal CustomUserDetails currentUser
    ) {
        List<VesselTypeStats> stats = vesselTypeStatsService.getAllVesselTypeStats(currentUser, filters);

        return ResponseEntity.ok(stats);
    }
}