package com.iem.backend.dto;

public record FileUploadResponse(String path, String originalFilename, long sizeBytes) {
}
