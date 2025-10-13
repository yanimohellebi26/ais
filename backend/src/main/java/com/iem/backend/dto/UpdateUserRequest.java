package com.iem.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;

public record UpdateUserRequest(

    @NotNull(message = "User ID is required")
    @JsonProperty("id")
    Integer id,

    @Pattern(
            regexp = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)(?=.*[^A-Za-z0-9]).{8,}$",
            message = "Password must be at least 8 characters long and include upper, lower, digit, and special character"
    )
    @JsonProperty("password")
    String password,

    @JsonProperty("role")
    String role
) {
}