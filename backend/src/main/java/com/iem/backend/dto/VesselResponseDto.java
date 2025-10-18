package com.iem.backend.dto;

import com.iem.backend.entity.TransceiverClass;
import com.iem.backend.entity.Vessel;
import com.iem.backend.entity.VesselType;

import java.sql.Timestamp;
import java.util.Optional;

public record VesselResponseDto(
        Integer id,
        String mmsi,
        String imo,
        String vesselName,
        String callSign,
        Integer vesselType,
        String vesselTypeName,
        Integer cargoType,
        String cargoTypeName,
        Double length,
        Double width,
        Double draft,
        TransceiverClass transceiverClass,
        Timestamp baseDateTime,
        Boolean locked
) {
    public static VesselResponseDto fromEntity(Vessel v) { 
        return new VesselResponseDto(
                v.getId(),
                v.getMmsi(),
                v.getImo(),
                v.getVesselName(),
                v.getCallSign(),
                Optional.ofNullable(v.getVesselType()).map(VesselType::getId).orElse(0),
                Optional.ofNullable(v.getVesselType()).map(VesselType::getDescription).orElse("Unknown"),
                Optional.ofNullable(v.getCargoType()).map(VesselType::getId).orElse(0),
                Optional.ofNullable(v.getCargoType()).map(VesselType::getDescription).orElse("Unknown"),
                v.getLength(),
                v.getWidth(),
                v.getDraft(),
                v.getTransceiverClass(),
                v.getBaseDateTime(),
                v.isLocked()
        );
    }
}
