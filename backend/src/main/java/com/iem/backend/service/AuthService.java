package com.iem.backend.service;

import com.iem.backend.config.JwtUtil;
import com.iem.backend.dto.RegisterRequest;
import com.iem.backend.dto.RegisterResponse;
import com.iem.backend.dto.TokenRequest;
import com.iem.backend.dto.TokenResponse;
import com.iem.backend.entity.Role;
import com.iem.backend.entity.User;
import com.iem.backend.repository.RoleRepository;
import com.iem.backend.repository.UserAccountRepository;
import com.iem.backend.utils.ApiLogger;
import org.springframework.http.HttpStatus;
import org.springframework.security.authentication.*;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.security.core.Authentication;

@Service
public class AuthService {


    private final AuthenticationManager authenticationManager;
    private final JwtUtil jwtUtils;

    private final UserAccountRepository userAccountRepository;
    private final RoleRepository roleRepository;
    private final PasswordEncoder passwordEncoder;
    private final ApiLogger apiLogger;

    /**
     * Initializes the authentication service with required dependencies.
     *
     * @param userAccountRepository repository for managing user accounts
     * @param roleRepository repository for managing user roles
     * @param passwordEncoder encoder for hashing user passwords
     * @param apiLogger custom logger for API operations
     * @param jwtUtils utility for handling JWT creation and validation
     * @param authenticationManager authentication manager for verifying credentials
     */
    public AuthService(UserAccountRepository userAccountRepository,
                       RoleRepository roleRepository,
                       PasswordEncoder passwordEncoder,
                       ApiLogger apiLogger,
                       JwtUtil jwtUtils,
                       AuthenticationManager authenticationManager) {
        this.userAccountRepository = userAccountRepository;
        this.roleRepository = roleRepository;
        this.passwordEncoder = passwordEncoder;
        this.apiLogger = apiLogger;
        this.jwtUtils = jwtUtils;
        this.authenticationManager = authenticationManager;
    }

    /**
     * Registers a new user account after validating input and checking for duplicates.
     *
     * @param request registration details (username, email, password, role)
     * @return details of the newly created user
     * @throws ResponseStatusException if the email or username already exists, or the role is invalid
     */
    @Transactional
    public RegisterResponse register(RegisterRequest request) {
        String username = request.username().trim();
        String email = request.email().trim().toLowerCase();
        String roleName = request.role().trim();

        if (userAccountRepository.existsByEmailIgnoreCase(email)) {
            throw new ResponseStatusException(HttpStatus.CONFLICT, "Email already in use");
        }

        if (userAccountRepository.existsByUsernameIgnoreCase(username)) {
            throw new ResponseStatusException(HttpStatus.CONFLICT, "Username already in use");
        }

        Role role = roleRepository.findByNameIgnoreCase(roleName)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.BAD_REQUEST, "Unknown role"));

        User user = new User();
        user.setUsername(username);
        user.setEmail(email);
        user.setRole(role);
        user.setPasswordHash(passwordEncoder.encode(request.password()));

        User saved = userAccountRepository.save(user);
        apiLogger.success("User registered: " + saved.getEmail());

        return new RegisterResponse(saved.getId(), saved.getUsername(), saved.getEmail(), saved.getRole().getName());
    }

    /**
     * Authenticates a user and generates a JWT token upon successful login.
     *
     * @param request login credentials (email and password)
     * @return a JWT token response
     */
    public TokenResponse login(TokenRequest request){
        String email = request.email();
        String password = request.password();
        Authentication authentication = authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(
                        email,
                        password
                )
        );
        UserDetails userDetails = (UserDetails) authentication.getPrincipal();
        TokenResponse response = new TokenResponse(jwtUtils.generateToken(userDetails.getUsername()));
        return response;
    }


}
