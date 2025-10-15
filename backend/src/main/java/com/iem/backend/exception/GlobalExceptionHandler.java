package com.iem.backend.exception;

import com.iem.backend.dto.ApiError;
import jakarta.servlet.http.HttpServletRequest;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.util.ClassUtils;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.web.multipart.MaxUploadSizeExceededException;

@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final Class<?> ACCESS_DENIED_EXCEPTION = resolveClass("org.springframework.security.access.AccessDeniedException");
    private static final Class<?> AUTH_CREDENTIALS_NOT_FOUND_EXCEPTION = resolveClass("org.springframework.security.authentication.AuthenticationCredentialsNotFoundException");

    // Custom exception
    @ExceptionHandler(ApiException.class)
    public ResponseEntity<ApiError> handleApiException(ApiException ex, HttpServletRequest request) {
        log.warn("API Exception [{}]: {} - {}", ex.getClass().getSimpleName(), ex.getStatus(), ex.getMessage());

        ApiError error = new ApiError(
                ex.getStatus(),
                ex.getMessage(),
                request.getRequestURI()
        );
        return ResponseEntity.status(ex.getStatus()).body(error);
    }

    // ResponseStatusException handler
    @ExceptionHandler(ResponseStatusException.class)
    public ResponseEntity<ApiError> handleResponseStatusException(ResponseStatusException ex, HttpServletRequest request) {
        log.warn("ResponseStatusException [{}]: {}", ex.getStatusCode(), ex.getReason());

        ApiError error = new ApiError(
                (HttpStatus) ex.getStatusCode(),
                ex.getReason(),
                request.getRequestURI()
        );
        return ResponseEntity.status(ex.getStatusCode()).body(error);
    }

    @ExceptionHandler(MaxUploadSizeExceededException.class)
    public ResponseEntity<ApiError> handleMaxUploadSize(MaxUploadSizeExceededException ex, HttpServletRequest request) {
        log.warn("File upload rejected: payload too large");
        ApiError error = new ApiError(
                HttpStatus.PAYLOAD_TOO_LARGE,
                "Maximum upload size exceeded (10 MB)",
                request.getRequestURI()
        );
        return ResponseEntity.status(HttpStatus.PAYLOAD_TOO_LARGE).body(error);
    }

    // DTOs validation
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiError> handleValidationExceptions(MethodArgumentNotValidException ex, HttpServletRequest request) {
        StringBuilder errors = new StringBuilder();
        for (FieldError error : ex.getBindingResult().getFieldErrors()) {
            errors.append(error.getField()).append(": ").append(error.getDefaultMessage()).append("; ");
        }
        log.warn("Validation failed: {}", errors);

        ApiError errorResponse = new ApiError(
                HttpStatus.BAD_REQUEST,
                errors.toString(),
                request.getRequestURI()
        );
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(errorResponse);
    }

    // Fallback for unexpected exceptions
    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiError> handleOtherExceptions(Exception ex, HttpServletRequest request) {
        if (ACCESS_DENIED_EXCEPTION != null && ACCESS_DENIED_EXCEPTION.isInstance(ex)) {
            log.warn("Access denied: {}", ex.getMessage());
            ApiError error = new ApiError(
                    HttpStatus.FORBIDDEN,
                    "Access denied: insufficient permissions.",
                    request.getRequestURI()
            );
            return ResponseEntity.status(HttpStatus.FORBIDDEN).body(error);
        }

        if (AUTH_CREDENTIALS_NOT_FOUND_EXCEPTION != null && AUTH_CREDENTIALS_NOT_FOUND_EXCEPTION.isInstance(ex)) {
            log.warn("Unauthorized access attempt: {}", ex.getMessage());
            ApiError error = new ApiError(
                    HttpStatus.UNAUTHORIZED,
                    "Authentication required.",
                    request.getRequestURI()
            );
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(error);
        }

        log.error("Unhandled Exception", ex);
        ApiError error = new ApiError(
                HttpStatus.INTERNAL_SERVER_ERROR,
                "Internal server error",
                request.getRequestURI()
        );
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
    }

    private static Class<?> resolveClass(String className) {
        try {
            return ClassUtils.forName(className, GlobalExceptionHandler.class.getClassLoader());
        } catch (ClassNotFoundException ex) {
            return null;
        }
    }
}
