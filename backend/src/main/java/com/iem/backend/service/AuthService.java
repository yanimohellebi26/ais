package com.iem.backend.service;

import com.iem.backend.config.JwtUtil;
import com.iem.backend.dto.RegisterRequest;
import com.iem.backend.dto.TokenRequest;
import com.iem.backend.dto.TokenResponse;
import com.iem.backend.dto.UserDTO;
import com.iem.backend.entity.Role;
import com.iem.backend.entity.User;
import com.iem.backend.repository.RoleRepository;
import com.iem.backend.repository.UserRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.security.authentication.*;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.security.core.Authentication;

@Service
@Slf4j
public class AuthService {


    private final AuthenticationManager authenticationManager;
    private final JwtUtil jwtUtils;

    private final UserRepository userRepository;
    private final RoleRepository roleRepository;
    private final PasswordEncoder passwordEncoder;

    /**
     * Initializes the authentication service with required dependencies.
     *
     * @param userRepository repository for managing user accounts
     * @param roleRepository repository for managing user roles
     * @param passwordEncoder encoder for hashing user passwords
     * @param jwtUtils utility for handling JWT creation and validation
     * @param authenticationManager authentication manager for verifying credentials
     */
    public AuthService(UserRepository userRepository,
                       RoleRepository roleRepository,
                       PasswordEncoder passwordEncoder,
                       JwtUtil jwtUtils,
                       AuthenticationManager authenticationManager) {
        this.userRepository = userRepository;
        this.roleRepository = roleRepository;
        this.passwordEncoder = passwordEncoder;
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
    public UserDTO register(RegisterRequest request) {
        String username = request.username().trim();
        String email = request.email().trim().toLowerCase();
        String roleName = request.role().trim();

        if (userRepository.existsByEmailIgnoreCase(email)) {
            throw new ResponseStatusException(HttpStatus.CONFLICT, "Email already in use");
        }

        if (userRepository.existsByUsernameIgnoreCase(username)) {
            throw new ResponseStatusException(HttpStatus.CONFLICT, "Username already in use");
        }

        if ("ADMIN".equals(roleName)) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN, "Cannot assign ADMIN role directly");
        }

        Role role = roleRepository.findByNameIgnoreCase(roleName)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.BAD_REQUEST, "Unknown role"));

        User user = new User();
        user.setUsername(username);
        user.setEmail(email);
        user.setRole(role);
        user.setPasswordHash(passwordEncoder.encode(request.password()));

        User saved = userRepository.save(user);
        log.info("User registered: {}", saved.getEmail());

        return new UserDTO(saved.getId(), saved.getUsername(), saved.getEmail(), saved.getRole().getName(), null, null, null);
    }

    /**
     * Authenticates a user and generates a JWT token upon successful login.
     *
     * @param request login credentials (email and password)
     * @return a JWT token response
     */
    public TokenResponse login(TokenRequest request) {
        Authentication authentication = authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(
                        request.email(),
                        request.password()
                )
        );

        UserDetails userDetails = (UserDetails) authentication.getPrincipal();

        String role = userDetails.getAuthorities().stream()
                .findFirst()
                .map(GrantedAuthority::getAuthority)
                .orElse("ROLE_USER"); // Valeur par défaut

        String token = jwtUtils.generateToken(userDetails.getUsername(), role);
        return new TokenResponse(token);
    }


}
