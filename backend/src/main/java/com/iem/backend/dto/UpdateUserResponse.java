package com.iem.backend.dto;

import java.time.OffsetDateTime;

import com.fasterxml.jackson.annotation.JsonProperty;

public record UpdateUserResponse(

    @JsonProperty("id")
    Integer id,
    
    @JsonProperty("email")
    String email,

    @JsonProperty("role")
    String role,
    
    @JsonProperty("last_update")
    OffsetDateTime lastUpdate

) {
}
