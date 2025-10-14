package com.iem.backend.exception;

import org.springframework.http.HttpStatus;

public class UserAccessDeniedException extends ApiException {

    public UserAccessDeniedException(String message, HttpStatus status) {
        super(message, status);
    }

    public UserAccessDeniedException() {
        super("Acces denied", HttpStatus.UNAUTHORIZED); //pas connecté
    }
   
    public UserAccessDeniedException(String message) {
        super(message, HttpStatus.FORBIDDEN); //connecté mais pas authorisé noob
    }


}
