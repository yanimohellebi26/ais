package com.iem.backend.dto;

import com.iem.backend.entity.TransceiverClass;
import com.iem.backend.entity.Vessel;
import com.iem.backend.entity.VesselType;

import jakarta.validation.constraints.PositiveOrZero;
import jakarta.validation.constraints.Size;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;


import java.sql.Timestamp;
import java.util.Optional;

public record RequestVesselDto(
        Integer id,

        @NotBlank(message = "MMSI is required")
        @Size(max = 9, message = "MMSI must not exceed 9 characters")
        String mmsi,

        @NotBlank(message = "IMO is required")
        @Size(max = 20, message = "IMO must not exceed 20 characters")
        String imo,

        @NotBlank(message = "Vessel name is required")
        @Size(max = 100, message = "Vessel name must not exceed 100 characters")
        String vesselName,

        @NotBlank(message = "Call sign is required")
        @Size(max = 20, message = "Call sign must not exceed 20 characters")
        String callSign,

        Integer vesselType,
        String vesselTypeName,
        Integer cargoType,
        String cargoTypeName,

        @PositiveOrZero(message = "Length must be positive")
        Double length,

        @PositiveOrZero(message = "Width must be positive")
        Double width,

        @PositiveOrZero(message = "Draft must be positive")
        Double draft,

        @NotNull(message = "Transceiver class is required")
        TransceiverClass transceiverClass,

        Timestamp baseDateTime,

        Boolean locked
) {
    public static RequestVesselDto fromEntity(Vessel v) { 
        return new RequestVesselDto(
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
