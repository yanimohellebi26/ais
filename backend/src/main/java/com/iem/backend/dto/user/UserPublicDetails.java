package com.iem.backend.dto.user;

public record UserPublicDetails(
        Integer id,
        String username,
        String email,
        String role
)
{ }
