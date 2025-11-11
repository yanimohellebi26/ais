package com.iem.backend.exception;

import org.springframework.http.HttpStatus;

public class PositionVesselNotFoundException extends ApiException{

    public PositionVesselNotFoundException() { super("Position vessel not found", HttpStatus.NOT_FOUND); }

    public PositionVesselNotFoundException(String message) {
        super(message, HttpStatus.NOT_FOUND);
    }
}