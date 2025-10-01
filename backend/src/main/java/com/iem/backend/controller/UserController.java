package com.iem.backend.controller;

import com.iem.backend.dto.UpdateUserRequest;
import com.iem.backend.model.User;
import com.iem.backend.service.UserService;
import com.iem.backend.utils.ApiLogger;
import org.springframework.http.ResponseEntity;
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

    @PutMapping
    public ResponseEntity<?> updateUser(@RequestBody UpdateUserRequest request) {
        try {
            User currentUser = new User();
            currentUser.setUsername("admin");
            currentUser.setRole("admin");

            User updatedUser = userService.updateUser(request, currentUser);

            apiLogger.success("Utilisateur" + updatedUser.getUsername() + " mis à jour par " + currentUser.getUsername());

            return ResponseEntity.ok(updatedUser);
        } catch (RuntimeException e) {
            apiLogger.error("Erreur de mise à joueur de l'utilisateur", e);
            return ResponseEntity.badRequest().body(e.getMessage());
        }
    }
}
