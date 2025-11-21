package com.iem.backend.dto.requestProperty;

import java.time.OffsetDateTime;

public record RequestPropertyDetails(
        Integer id,
        Integer userId,
        String username,
        String userEmail,
        String userRole,
        String mmsi,
        Integer fileId,
        String fileName,
        OffsetDateTime createdAt
) {}
