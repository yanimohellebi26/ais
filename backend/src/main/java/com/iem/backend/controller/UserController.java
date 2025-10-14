package com.iem.backend.controller;

import com.iem.backend.dto.DeleteUserResponse;
import com.iem.backend.dto.UpdateUserRequest;
import com.iem.backend.dto.UpdateUserResponse;
import com.iem.backend.dto.UserResponse;
import com.iem.backend.service.UserService;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import jakarta.validation.Valid;

import java.util.List;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/users")
public class UserController {

    private final UserService userService;

    public UserController(UserService userService) {
        this.userService = userService;
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

    @Operation(
        summary = "Delete an user",
        description = "Delete an user by ID, only by ADMIN users"
    )
    @ApiResponses(
        value = {
            @ApiResponse(responseCode = "200", description = "User Deleted Successfully"),
            @ApiResponse(responseCode = "403", description = "Access Denied : Requires ADMIN Role"),
            @ApiResponse(responseCode = "404", description = "User Not Found")
        }
    )
    @DeleteMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<DeleteUserResponse> deleteUser(@PathVariable Integer id) {
        DeleteUserResponse response = userService.deleteUserById(id);
        return ResponseEntity.ok(response);
    }
    
    @Operation(
        summary = "Visualize all users",
        description = "Visualizes all users in the database, only by ADMIN users"
    )
    @ApiResponses(
        value = {
            @ApiResponse(responseCode = "200", description = "Users Visualized Successfuly"),
            @ApiResponse(responseCode = "403", description = "Access Denied : Requires ADMIN Role")
        }
    )
    @GetMapping
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<List<UserResponse>> getAllUsers() {
        return ResponseEntity.ok(userService.getAllUsers());
    }
}
