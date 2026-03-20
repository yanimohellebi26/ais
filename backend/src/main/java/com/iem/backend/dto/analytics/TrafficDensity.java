package com.iem.backend.dto.analytics;

public record TrafficDensity(
        double lat,
        double lon,
        long density
) {}