package com.iem.backend.dto;

import com.fasterxml.jackson.annotation.JsonFormat;
import org.springframework.http.HttpStatus;
import java.time.OffsetDateTime;

public record ApiError(
        Integer statusCode,
        String message,
        String path,
        @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd'T'HH:mm:ssXXX")
        OffsetDateTime timestamp
) {
    public ApiError(HttpStatus status, String message, String path) {
        this(status.value(), message, path, OffsetDateTime.now());
    }
}
