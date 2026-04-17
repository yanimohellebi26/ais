package com.iem.backend.repository.projection;

import java.time.LocalDate;

public interface SeasonalityProjection {
    Integer getValue();
    Integer getYear();
    LocalDate getDate();
    LocalDate getEndDate();
    Long getTrajectoryCount();
}