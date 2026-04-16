package com.iem.backend.controller;

import com.iem.backend.dto.analytics.AnalyticsFilter;
import com.iem.backend.dto.statistics.Seasonality;
import com.iem.backend.dto.statistics.VesselTypeStats;
import com.iem.backend.entity.CustomUserDetails;
import com.iem.backend.service.StatisticsService;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/statistics")
public class StatisticsController {

    private final StatisticsService vesselTypeStatsService;
    private final StatisticsService seasonalityService;

    public StatisticsController(StatisticsService vesselTypeStatsService, StatisticsService seasonalityService) {
        this.vesselTypeStatsService = vesselTypeStatsService;
        this.seasonalityService = seasonalityService;
    }

    @PostMapping("/vessel-type-statistics")
    public ResponseEntity<List<VesselTypeStats>> getVesselTypeStats(
            @RequestBody AnalyticsFilter filters,
            @RequestParam(defaultValue = "10") int topN,
            @AuthenticationPrincipal CustomUserDetails currentUser
    ) {
        List<VesselTypeStats> stats = vesselTypeStatsService.getAllVesselTypeStats(currentUser, filters, topN);

        return ResponseEntity.ok(stats);
    }

    @PostMapping("/seasonality")
    public ResponseEntity<List<Seasonality>> getSeasonalityStats(
            @RequestBody AnalyticsFilter filters,
            @AuthenticationPrincipal CustomUserDetails currentUser
    ){
        List<Seasonality> seasonality = seasonalityService.getSeasonality(currentUser, filters);

        return ResponseEntity.ok(seasonality);
    }
}