package com.iem.backend.dto.statistics;

import java.time.LocalDate;

public record Seasonality(
        Integer value,
        Integer year,
        LocalDate date,
        LocalDate endDate,
        Long trajectoryCount,
        String granularity
) {
}