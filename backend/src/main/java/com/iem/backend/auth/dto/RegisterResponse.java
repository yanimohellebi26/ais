package com.iem.backend.auth.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public record RegisterResponse(
        @JsonProperty("id")
        Long id,
        @JsonProperty("username")
        String username,
        @JsonProperty("email")
        String email,
        @JsonProperty("role")
        String role
) {
}
