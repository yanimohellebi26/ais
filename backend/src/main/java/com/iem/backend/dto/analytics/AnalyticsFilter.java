package com.iem.backend.dto.analytics;

import java.sql.Timestamp;

public record AnalyticsFilter(
        Timestamp startDate,
        Timestamp endDate,
        Integer vesselType,
        String vesselGroup,
        String country,
        Double latitude,
        Double longitude,
        Double radius
) {
}
