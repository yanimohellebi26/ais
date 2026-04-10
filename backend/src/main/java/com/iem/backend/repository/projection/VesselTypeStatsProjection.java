package com.iem.backend.repository.projection;

public interface VesselTypeStatsProjection {
    Integer getVesselTypeId();
    String getVesselTypeDescription();
    String getVesselGroup();
    Long getTrajectoryCount();
    Double getTotalDistanceKm();
    Double getAvgSpeedKmh();
    Double getAvgDistanceKm();
    Double getTotalDurationHours();
    Double getAvgDurationHours();
    Double getEfficiencyKmh();
}
