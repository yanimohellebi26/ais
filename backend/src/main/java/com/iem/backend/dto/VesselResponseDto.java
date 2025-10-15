package com.iem.backend.dto;

import com.iem.backend.entity.Vessel;

public record VesselResponseDto(
        Integer id,
        String mmsi,
        String imo,
        String vesselName,
        String callSign,
        String vesselTypeName,
        Boolean locked
) {
    public static VesselResponseDto fromEntity(Vessel v) {
        return new VesselResponseDto(
                v.getId(),
                v.getMmsi(),
                v.getImo(),
                v.getVesselName(),
                v.getCallSign(),
                v.getVesselType() != null ? v.getVesselType().getDescription() : null,
                v.isLocked()
        );
    }
}
