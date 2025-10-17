package com.iem.backend.dto;

import java.time.OffsetDateTime;

import com.fasterxml.jackson.annotation.JsonProperty;

public record DeleteUserResponse (
        
        @JsonProperty("id")
        Integer id,

        @JsonProperty("username")
        String username,

        @JsonProperty("email")
        String email,

        @JsonProperty("role")
        String role,

        @JsonProperty("deleted_at")
        OffsetDateTime deletedAt
) {
}
