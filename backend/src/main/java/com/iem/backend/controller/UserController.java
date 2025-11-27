package com.iem.backend.controller;

import com.iem.backend.dto.user.UpdateUserRequest;
import com.iem.backend.dto.user.UpdateUserPasswordRequest;
import com.iem.backend.dto.user.UserResponse;
import com.iem.backend.entity.CustomUserDetails;
import com.iem.backend.service.UserService;

import jakarta.validation.Valid;

import java.util.List;

import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/users")
public class UserController {

    private final UserService userService;

    public UserController(UserService userService) {
        this.userService = userService;
    }

    @PutMapping
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<UserResponse> updateUser(@Valid @RequestBody UpdateUserRequest dto) {
        return ResponseEntity.ok(userService.updateUser(dto));
    }

    @GetMapping("/{id}")
    public ResponseEntity<UserResponse> getUserById(@PathVariable Integer id, @AuthenticationPrincipal CustomUserDetails currentUser) {
        return ResponseEntity.ok(userService.getUserById(id, currentUser));
    }

    @PutMapping("/{id}/password")
    public ResponseEntity<Void> updatePassword(@PathVariable Integer id,
                                               @Valid @RequestBody UpdateUserPasswordRequest dto,
                                               @AuthenticationPrincipal CustomUserDetails currentUser) {
        userService.updatePassword(id, dto, currentUser);
        return ResponseEntity.noContent().build();
    }

    @DeleteMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Void> deleteUserById(@PathVariable Integer id) {
        userService.deleteUserById(id);
        return ResponseEntity.noContent().build();
    }

    @GetMapping
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<List<UserResponse>> getAllUsers() {
        return ResponseEntity.ok(userService.getAllUsers());
    }
}
