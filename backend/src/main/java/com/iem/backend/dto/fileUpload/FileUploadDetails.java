package com.iem.backend.dto.fileUpload;

import java.time.OffsetDateTime;

public record FileUploadDetails (
        Integer id,
        Integer userId,
        String originalFilename,
        Long fileSize,
        OffsetDateTime uploadedAt
) {}
