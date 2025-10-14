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

    //UC-07 GET user by id (self ou admin)
    @Operation(
        summary = "get user by id",
        description = "user can acces now own account or admin can acces any account"
    )
    @ApiResponses(
        value = {
            @ApiResponse(responseCode = "200", description = "User retrieved successfully"),
            @ApiResponse(responseCode = "403", description = "Access denied: user cannot access this account"),
            @ApiResponse(responseCode = "404", description = "User not found")
        }
    )
    @GetMapping("/{id}")
    public ResponseEntity<UpdateUserResponse> getUserById(@PathVariable Long id,Principal principal){//@pathvariable long id = id courant et principal = user connecté
        UpdateUserResponse user = userService.getUserById(id,principal);
        return ResponseEntity.ok(user);
    }

    //UC-07 PUT password 
    @Operation(
        summary = "update own password",
        description = "uer can update their password only"
    )
    @ApiResponses(
        value = {
            @ApiResponse(responseCode = "204", description = "Password updated successfully"),
            @ApiResponse(responseCode = "400", description = "Invalid request or validation failed"),
            @ApiResponse(responseCode = "403", description = "Access denied: user cannot update this password"),
            @ApiResponse(responseCode = "404", description = "User not found")
    })
    @PutMapping("/{id}/password")
    public ResponseEntity<Void> updatePassword(@PathVariable Long id,
                                               @Valid @RequestBody UpdatePasswordRequest dto,
                                               Principal principal) {
        userService.updatePassword(id, dto, principal);
        return ResponseEntity.noContent().build(); 
    }

}
