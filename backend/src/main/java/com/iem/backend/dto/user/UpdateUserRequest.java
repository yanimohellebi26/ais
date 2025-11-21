package com.iem.backend.dto.user;


import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;

public record UpdateUserRequest(

    @NotNull
    Integer id,

    @Pattern(
            regexp = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)(?=.*[^A-Za-z0-9]).{8,}$",
            message = "Password must be at least 8 characters long and include upper, lower, digit, and special character"
    )
    String password,

    String role
) {
}