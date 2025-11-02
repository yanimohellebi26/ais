package com.iem.backend.exception;

import org.springframework.http.HttpStatus;

public class VesselAlreadyOwnedException extends ApiException {

    public VesselAlreadyOwnedException(String message, HttpStatus status) {
        super(message, status);
    }

    public VesselAlreadyOwnedException() {
        super("Vessel already owned", HttpStatus.BAD_REQUEST);
    }


}
