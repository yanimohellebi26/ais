package com.iem.backend.dto.statistics;

public record VesselTypeStats(
        Integer vesselTypeId,
        String vesselTypeDescription,
        String vesselGroup,
        Long trajectoryCount,
        Double totalDistanceKm,
        Double avgSpeedKmh,
        Double avgDistanceKm,
        Double totalDurationHours,
        Double avgDurationHours,
        Double efficiencyKmh
) {
}