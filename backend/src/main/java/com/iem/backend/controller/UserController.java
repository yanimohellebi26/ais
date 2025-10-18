package com.iem.backend.controller;

import com.fasterxml.jackson.annotation.JsonView;
import com.iem.backend.dto.UpdateUserRequest;
import com.iem.backend.dto.UpdatePasswordRequest;
import com.iem.backend.service.UserService;
import com.iem.backend.utils.ApiLogger;
import com.iem.backend.dto.UserDTO;
import com.iem.backend.dto.Views;
import com.iem.backend.service.UserService;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import jakarta.validation.Valid;
import java.security.Principal;

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
    @JsonView(Views.Update.class)
    public ResponseEntity<UserDTO> updateUser(@Valid @RequestBody UpdateUserRequest dto) {
        UserDTO updated = userService.updateUser(dto);
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
    @JsonView(Views.Public.class)
    public ResponseEntity<UserDTO> getUserById(@PathVariable int id,Principal principal){
        UserDTO user = userService.getUserById(id,principal);
        return ResponseEntity.ok(user);
    }

    //UC-07 PUT password 
    @Operation(
        summary = "update own password",
        description = "uer can update their password only"
    )
    @ApiResponses(
        value = {
            @ApiResponse(responseCode = "200", description = "Password updated successfully"),
            @ApiResponse(responseCode = "400", description = "Invalid request or validation failed"),
            @ApiResponse(responseCode = "403", description = "Access denied: user cannot update this password"),
            @ApiResponse(responseCode = "404", description = "User not found")
    })
    @PutMapping("/{id}/password")
    public ResponseEntity<String> updatePassword(@PathVariable int id,
                                               @Valid @RequestBody UpdatePasswordRequest dto,
                                               Principal principal) {
        userService.updatePassword(id, dto, principal);
        return ResponseEntity.ok("password update success"); 
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
    @JsonView(Views.Delete.class)
    public ResponseEntity<UserDTO> deleteUser(@PathVariable Integer id) {
        UserDTO response = userService.deleteUserById(id);
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
    @JsonView(Views.Admin.class)
    public ResponseEntity<List<UserDTO>> getAllUsers() {
        return ResponseEntity.ok(userService.getAllUsers());
    }
}
