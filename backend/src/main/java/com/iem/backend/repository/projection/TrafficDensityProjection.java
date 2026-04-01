package com.iem.backend.repository.projection;

public interface TrafficDensityProjection {
    double getLat();
    double getLon();
    long getDensity();
}