package com.iem.backend.dto.analytics;

import java.time.LocalDate;

public record AnalyticsFilter(
        LocalDate startDate,
        LocalDate endDate,
        Integer vesselType,
        String vesselGroup,
        String country,
        Double latitude,
        Double longitude,
        Double radius
) {
}
