package com.iem.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

public record RegisterRequest(
        @NotBlank(message = "Username is required")
        @Size(max = 50, message = "Username must not exceed 50 characters")
        @JsonProperty("username")
        String username,

        @NotBlank(message = "Email is required")
        @Email(message = "Email must be valid")
        @JsonProperty("email")
        String email,

        @NotBlank(message = "Password is required")
        @Pattern(
                regexp = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)(?=.*[^A-Za-z0-9]).{8,}$",
                message = "Password must be at least 8 characters long and include upper, lower, digit, and special character"
        )
        @JsonProperty("password")
        String password,

        @NotBlank(message = "Role is required")
        @JsonProperty("role")
        String role
) {
}
