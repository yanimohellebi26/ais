package com.iem.backend.dto;

public record FileUploadResponse(Integer id, String path, String originalFilename, long sizeBytes) {
}
