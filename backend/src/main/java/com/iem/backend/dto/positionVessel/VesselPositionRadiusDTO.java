package com.iem.backend.dto.positionVessel;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonView;
import com.iem.backend.dto.Views;

import java.sql.Timestamp;

public record VesselPositionRadiusDTO(
        @JsonView(Views.Public.class)
        @JsonProperty("mmsi")
        String mmsi,

        @JsonView(Views.Public.class)
        @JsonProperty("latitude")
        Double latitude,

        @JsonView(Views.Public.class)
        @JsonProperty("longitude")
        Double longitude,

        @JsonView(Views.Public.class)
        @JsonProperty("distance_km")
        Double distanceKm,

        @JsonView(Views.Public.class)
        @JsonProperty("timestamp")
        Timestamp timestamp
) {
}