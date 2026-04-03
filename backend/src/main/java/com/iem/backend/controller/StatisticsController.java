package com.iem.backend.controller;

import com.iem.backend.dto.analytics.AnalyticsFilter;
import com.iem.backend.dto.statistics.VesselTypeStats;
import com.iem.backend.entity.CustomUserDetails;
import com.iem.backend.service.VesselTypeStatsService;
import org.springdoc.core.annotations.ParameterObject;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/v1/statistics")
public class StatisticsController {

    private final VesselTypeStatsService vesselTypeStatsService;

    public StatisticsController(VesselTypeStatsService vesselTypeStatsService) {
        this.vesselTypeStatsService = vesselTypeStatsService;
    }

    @GetMapping("/vessel_type")
    public ResponseEntity<List<VesselTypeStats>> getVesselTypeStats(
            @ModelAttribute @ParameterObject AnalyticsFilter filters,
            @AuthenticationPrincipal CustomUserDetails currentUser
    ) {
        List<VesselTypeStats> stats = vesselTypeStatsService.getVesselTypeStats(currentUser, filters);

        return ResponseEntity.ok(stats);
    }
}