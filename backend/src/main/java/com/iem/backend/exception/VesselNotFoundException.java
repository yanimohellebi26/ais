package com.iem.backend.exception;

import org.springframework.http.HttpStatus;

public class VesselNotFoundException extends ApiException {
    public VesselNotFoundException() {
        super("Vessel not found", HttpStatus.BAD_REQUEST);
    }

    public VesselNotFoundException(String message) {
        super(message, HttpStatus.NOT_FOUND);
    }

}
