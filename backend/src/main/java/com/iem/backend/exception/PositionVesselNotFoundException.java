package com.iem.backend.exception;

public class PositionVesselNotFoundException extends RuntimeException {
  public PositionVesselNotFoundException(String message) {
    super(message);
  }
}
