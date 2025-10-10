package com.iem.backend.dto;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class UpdateUserRequest {

    private Integer id;
    private String password;
    private String role;

}