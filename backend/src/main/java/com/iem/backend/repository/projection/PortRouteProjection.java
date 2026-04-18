package com.iem.backend.repository.projection;

public interface PortRouteProjection {
    Integer getSrcPortId();
    String getSrcPortName();
    Integer getDestPortId();
    String getDestPortName();
    Long getShipCount();
    Double getAvgDuration();
    String getGeojson();
}
