package com.iem.backend.service;

import com.iem.backend.config.JwtUtil;
import com.iem.backend.dto.user.RegisterRequest;
import com.iem.backend.dto.user.LoginRequest;
import com.iem.backend.dto.user.TokenResponse;
import com.iem.backend.dto.user.UserResponse;
import com.iem.backend.entity.Role;
import com.iem.backend.entity.User;
import com.iem.backend.exception.ApiExceptions;
import com.iem.backend.mapper.UserMapper;
import com.iem.backend.repository.RoleRepository;
import com.iem.backend.repository.UserRepository;

import lombok.extern.slf4j.Slf4j;
import org.springframework.security.authentication.*;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.security.core.Authentication;

@Service
@Slf4j
public class AuthService {

    private final AuthenticationManager authenticationManager;
    private final JwtUtil jwtUtils;
    private final UserRepository userRepository;
    private final RoleRepository roleRepository;
    private final PasswordEncoder passwordEncoder;
    private final UserMapper userMapper;

    public AuthService(UserRepository userRepository,
                       RoleRepository roleRepository,
                       PasswordEncoder passwordEncoder,
                       JwtUtil jwtUtils,
                       AuthenticationManager authenticationManager,
                       UserMapper userMapper) {

        this.userRepository = userRepository;
        this.roleRepository = roleRepository;
        this.passwordEncoder = passwordEncoder;
        this.jwtUtils = jwtUtils;
        this.authenticationManager = authenticationManager;
        this.userMapper = userMapper;
    }

    @Transactional
    public UserResponse register(RegisterRequest dto) {

        String username = dto.username().trim();
        String email = dto.email().trim().toLowerCase();

        if (userRepository.existsByEmailIgnoreCase(email)) {
            throw new ApiExceptions.ConflictException("Email already in use");
        }
        if (userRepository.existsByUsernameIgnoreCase(username)) {
            throw new ApiExceptions.ConflictException("Username already in use");
        }
        if ("ADMIN".equalsIgnoreCase(dto.role())) {
            throw new ApiExceptions.ForbiddenException("Cannot assign ADMIN role directly");
        }

        Role role = roleRepository.findByNameIgnoreCase(dto.role())
                .orElseThrow(() -> new ApiExceptions.BadRequestException("Unknown role"));

        User user = new User();
        user.setUsername(username);
        user.setEmail(email);
        user.setPasswordHash(passwordEncoder.encode(dto.password()));
        user.setRole(role);

        User saved = userRepository.save(user);

        return userMapper.toResponse(saved);
    }

    /**
     * Authenticates a user and generates a JWT token upon successful login.
     *
     * @param dto login credentials (email and password)
     * @return a JWT token response
     */
    public TokenResponse login(LoginRequest dto) {
        Authentication authentication = authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(
                        dto.email(),
                        dto.password()
                )
        );

        UserDetails userDetails = (UserDetails) authentication.getPrincipal();

        String role = userDetails.getAuthorities().stream()
                .findFirst()
                .map(GrantedAuthority::getAuthority)
                .orElse("ROLE_USER");

        Integer id = userRepository
                .findByEmailIgnoreCase(dto.email())
                .orElseThrow(() -> new ApiExceptions.NotFoundException("User not found"))
                .getId();


        String token = jwtUtils.generateToken(userDetails.getUsername(), role, id);
        return new TokenResponse(token);
    }

}
