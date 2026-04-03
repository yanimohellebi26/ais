package com.iem.backend.dto.statistics;

public record VesselTypeStats(
        Integer vesselTypeId,
        String vesselTypeDescription,
        String vesselGroup,
        Long trajectoryCount,
        Double totalDistanceKm,
        Double averageSpeedKmh
) {
}