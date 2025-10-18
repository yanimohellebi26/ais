package com.iem.backend.exception;

import org.springframework.http.HttpStatus;

public class RoleNotFoundException extends ApiException {
    
    public RoleNotFoundException() {
        super("Role Not Found", HttpStatus.NOT_FOUND);
    }

    public RoleNotFoundException(String role) {
        super("Role " + role + " Not Found", HttpStatus.NOT_FOUND);
    }
}
