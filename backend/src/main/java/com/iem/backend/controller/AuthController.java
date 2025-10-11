package com.iem.backend.controller;

import com.iem.backend.dto.RegisterRequest;
import com.iem.backend.dto.RegisterResponse;
import com.iem.backend.dto.TokenRequest;
import com.iem.backend.dto.TokenResponse;
import com.iem.backend.service.AuthService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/auth")
public class AuthController {

    private final AuthService authService;

    public AuthController(AuthService authService) {
        this.authService = authService;
    }

    @Operation(summary = "Register a user",
            description = "Create a new user in database")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "201", description = "User creation is a success"),
            @ApiResponse(responseCode = "400", description = "Error during registration")
    })
    @PostMapping("/register")
    public ResponseEntity<RegisterResponse> register(@Valid @RequestBody RegisterRequest request) {
        RegisterResponse response = authService.register(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    @Operation(summary = "Login as a user",
            description = "return a Token to use other endpoint")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "201", description = "Login is success and return Token"),
            @ApiResponse(responseCode = "400", description = "Error during login")
    })
    @PostMapping("/login")
    public ResponseEntity<TokenResponse> login(@Valid  @RequestBody TokenRequest request) {
        TokenResponse response = authService.login(request);
        return ResponseEntity.status(HttpStatus.OK).body(response);
    }
}
