package com.iem.backend.dto.positionVessel;


import lombok.Data;

import java.sql.Timestamp;

@Data
public class PositionVesselRadiusProperties {
    private Integer id;
    private String mmsi;
    private Double sog;
    private Double cog;
    private Short heading;
    private String status;
    private Timestamp baseDateTime;
    private Double distanceKm;
}