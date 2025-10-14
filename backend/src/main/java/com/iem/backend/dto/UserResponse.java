package com.iem.backend.dto;

import java.time.OffsetDateTime;

import com.fasterxml.jackson.annotation.JsonProperty;

public record UserResponse(
    
    @JsonProperty("id")
    Integer id,
    
    @JsonProperty("username")
    String username,

    @JsonProperty("email")
    String email,

    @JsonProperty("role")
    String role,
    
    @JsonProperty("created_at")
    OffsetDateTime createdAt,

    @JsonProperty("last_update")
    OffsetDateTime lastUpdate

) {   
}
