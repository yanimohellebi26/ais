package com.iem.backend.dto.user;

import java.time.OffsetDateTime;

public record UserResponse(
        Integer id,
        String username,
        String email,
        String role,
        OffsetDateTime createdAt,
        OffsetDateTime lastUpdate
) {}