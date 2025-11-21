package com.iem.backend.dto.vessel;

import com.iem.backend.entity.TransceiverClass;
import com.iem.backend.entity.Vessel;
import com.iem.backend.entity.VesselType;

import java.sql.Timestamp;
import java.util.Optional;

public record VesselDetails(
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
        Boolean locked,
        String country
) {}
