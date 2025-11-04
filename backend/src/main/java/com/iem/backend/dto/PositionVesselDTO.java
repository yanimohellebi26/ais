package com.iem.backend.dto;

import java.sql.Timestamp;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonView;
import com.iem.backend.entity.VesselStatus;

public record PositionVesselDTO(

    @JsonView(Views.Public.class)
    @JsonProperty("mmsi")
    String mmsi,

    @JsonView(Views.Public.class)
    @JsonProperty("baseDateTime")
    Timestamp baseDateTime,

    @JsonView(Views.Public.class)
    @JsonProperty("sog")
    Double sog,

    @JsonView(Views.Public.class)
    @JsonProperty("cog")
    Double cog,

    @JsonView(Views.Public.class)
    @JsonProperty("heading")
    Short heading,

    @JsonView(Views.Public.class)
    @JsonProperty("statusId")
    Integer statusId,

    @JsonView(Views.Public.class)
    @JsonProperty("latitude")
    Double latitude,

    @JsonView(Views.Public.class)
    @JsonProperty("longitude")
    Double longitude
) { 
}
