package com.iem.backend.exception;

import org.springframework.http.HttpStatus;

/**
 * Bundle of generics REST exception to cover major cases
 * Every exception extends from {@link ApiException}, and provide a message and {@link HttpStatus}
 */
public final class ApiExceptions {

    // 400 – BAD REQUEST
    public static class BadRequestException extends ApiException {
        public BadRequestException(String message) {
            super(message, HttpStatus.BAD_REQUEST);
        }
    }

    public static class MissingParameterException extends ApiException {
        public MissingParameterException(String message) {
            super(message, HttpStatus.BAD_REQUEST);
        }
    }

    // 401 – UNAUTHORIZED
    public static class UnauthorizedException extends ApiException {
        public UnauthorizedException(String message) {
            super(message, HttpStatus.UNAUTHORIZED);
        }
    }

    // 403 – FORBIDDEN
    public static class ForbiddenException extends ApiException {
        public ForbiddenException(String message) {
            super(message, HttpStatus.FORBIDDEN);
        }
    }

    // 404 – NOT FOUND
    public static class NotFoundException extends ApiException {
        public NotFoundException(String message) {
            super(message, HttpStatus.NOT_FOUND);
        }
    }

    // 409 – CONFLICT
    public static class ConflictException extends ApiException {
        public ConflictException(String message) {
            super(message, HttpStatus.CONFLICT);
        }
    }

    public static class AlreadyExistsException extends ApiException {
        public AlreadyExistsException(String message) {
            super(message, HttpStatus.CONFLICT);
        }
    }

    // 422 – UNPROCESSABLE ENTITY
    public static class BusinessRuleException extends ApiException {
        public BusinessRuleException(String message) {
            super(message, HttpStatus.UNPROCESSABLE_ENTITY);
        }
    }

    public static class InvalidStateException extends ApiException {
        public InvalidStateException(String message) {
            super(message, HttpStatus.UNPROCESSABLE_ENTITY);
        }
    }

    // 423 – LOCKED
    public static class ResourceLockedException extends ApiException {
        public ResourceLockedException(String message) {
            super(message, HttpStatus.LOCKED);
        }
    }

    // 500 – INTERNAL SERVER ERROR
    public static class InternalServerErrorException extends ApiException {
        public InternalServerErrorException(String message) {
            super(message, HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    // 503 – SERVICE UNAVAILABLE
    public static class ServiceUnavailableException extends ApiException {
        public ServiceUnavailableException(String message) {
            super(message, HttpStatus.SERVICE_UNAVAILABLE);
        }
    }

    // Private constructor to avoid container class instance
    private ApiExceptions() {}
}
