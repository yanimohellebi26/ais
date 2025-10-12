package com.iem.backend.dto;

import java.time.OffsetDateTime;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class UpdateUserResponse {
    
    private Integer id;
    private String email;
    private String role;
    private OffsetDateTime lastUpdate;

    public UpdateUserResponse(Integer id, String email, String role, OffsetDateTime lastUpdate) {
        this.id = id;
        this.email = email;
        this.role = role;
        this.lastUpdate = lastUpdate;
    }
}
