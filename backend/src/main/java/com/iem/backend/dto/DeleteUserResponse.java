package com.iem.backend.dto;

import java.time.OffsetDateTime;

public record DeleteUserResponse (
        Integer id,
        String username,
        String email,
        String role,
        OffsetDateTime deletedAt
) {
}
