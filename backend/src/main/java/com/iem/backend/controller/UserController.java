package com.iem.backend.controller;

import com.iem.backend.dto.UpdateUserRequest;
import com.iem.backend.entity.User;
import com.iem.backend.service.UserService;
import com.iem.backend.utils.ApiLogger;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/users")
public class UserController {

    private final UserService userService;
    private final ApiLogger apiLogger;

    @Autowired
    public UserController(UserService userService, ApiLogger apiLogger) {
        this.userService = userService;
        this.apiLogger = apiLogger;
    }

    @PutMapping
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<?> updateUser(@RequestBody UpdateUserRequest dto) {
        try {
            User updated = userService.updateUser(dto);
            return ResponseEntity.ok(updated);
        } catch (Exception e) {
            apiLogger.error("Failed to update user id " + dto.getId(), e);
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }
}
