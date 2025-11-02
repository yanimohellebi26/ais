package com.iem.backend.exception;

import org.springframework.http.HttpStatus;

public class FileNotFoundException extends ApiException {
    public FileNotFoundException() {
        super("File not found.", HttpStatus.NOT_FOUND);
    }
}
