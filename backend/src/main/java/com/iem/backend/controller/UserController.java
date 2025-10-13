package com.iem.backend.controller;

import com.iem.backend.dto.UpdateUserRequest;
import com.iem.backend.dto.UpdateUserResponse;
import com.iem.backend.service.UserService;
import com.iem.backend.utils.ApiLogger;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import jakarta.validation.Valid;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/users")
public class UserController {

    private final UserService userService;
    private final ApiLogger apiLogger;

    public UserController(UserService userService, ApiLogger apiLogger) {
        this.userService = userService;
        this.apiLogger = apiLogger;
    }

    @Operation(
        summary = "Update an user",
        description = "Update the user in the database, only by ADMIN users"
    )
    @ApiResponses(
        value = {
            @ApiResponse(responseCode = "200", description = "User Updated Successfuly"),
            @ApiResponse(responseCode = "400", description = "Invalid Request or Update Failed"),
            @ApiResponse(responseCode = "403", description = "Access Denied : Requires ADMIN Role"),
            @ApiResponse(responseCode = "404", description = "User Not Found")
        }
    )
    @PutMapping
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<UpdateUserResponse> updateUser(@Valid @RequestBody UpdateUserRequest dto) {
        UpdateUserResponse updated = userService.updateUser(dto);
        return ResponseEntity.status(HttpStatus.OK).body(updated);
    }
}
