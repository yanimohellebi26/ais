package com.iem.backend.exception;

import org.springframework.http.HttpStatus;

public class RequestPropertyNotFoundException extends ApiException {
    public RequestPropertyNotFoundException() {
        super("Request property not found.", HttpStatus.NOT_FOUND);
    }
}
