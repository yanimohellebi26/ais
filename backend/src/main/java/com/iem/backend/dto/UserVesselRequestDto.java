package com.iem.backend.dto;


import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.NotNull;

public record UserVesselRequestDto (

    @JsonProperty("userId")
    @NotNull
    Integer userId,

    @JsonProperty("mmsi")
    @NotNull
    String mmsi
) {

}

