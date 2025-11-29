package com.iem.backend.dto.vessel;

import com.iem.backend.dto.user.UserPublicDetails;
import com.iem.backend.entity.TransceiverClass;

import java.sql.Timestamp;
import java.util.List;

public record VesselUsersDetails(
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
        String country,
        List<UserPublicDetails> users
) {

}
