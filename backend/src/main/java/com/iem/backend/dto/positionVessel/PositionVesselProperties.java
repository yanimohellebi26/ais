package com.iem.backend.dto.positionVessel;


import java.sql.Timestamp;

public record PositionVesselProperties(
        String mmsi,
        Double sog,
        Double cog,
        Short heading,
        String status,
        Timestamp baseDateTime
) {}
