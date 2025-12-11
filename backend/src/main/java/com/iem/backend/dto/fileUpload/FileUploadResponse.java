package com.iem.backend.dto.fileUpload;

public record FileUploadResponse(
        Integer id,
        String path,
        String originalFilename,
        Long sizeBytes)
{}
