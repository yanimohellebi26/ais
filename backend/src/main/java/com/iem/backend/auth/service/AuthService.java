package com.iem.backend.auth.service;

import com.iem.backend.auth.dto.RegisterRequest;
import com.iem.backend.auth.dto.RegisterResponse;
import com.iem.backend.auth.entity.Role;
import com.iem.backend.auth.entity.UserAccount;
import com.iem.backend.auth.repository.RoleRepository;
import com.iem.backend.auth.repository.UserAccountRepository;
import com.iem.backend.utils.ApiLogger;
import org.springframework.http.HttpStatus;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

@Service
public class AuthService {

    private final UserAccountRepository userAccountRepository;
    private final RoleRepository roleRepository;
    private final PasswordEncoder passwordEncoder;
    private final ApiLogger apiLogger;

    public AuthService(UserAccountRepository userAccountRepository,
                       RoleRepository roleRepository,
                       PasswordEncoder passwordEncoder,
                       ApiLogger apiLogger) {
        this.userAccountRepository = userAccountRepository;
        this.roleRepository = roleRepository;
        this.passwordEncoder = passwordEncoder;
        this.apiLogger = apiLogger;
    }

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

        UserAccount user = new UserAccount();
        user.setUsername(username);
        user.setEmail(email);
        user.setRole(role);
        user.setPasswordHash(passwordEncoder.encode(request.password()));

        UserAccount saved = userAccountRepository.save(user);
        apiLogger.success("User registered: " + saved.getEmail());

        return new RegisterResponse(saved.getId(), saved.getUsername(), saved.getEmail(), saved.getRole().getName());
    }
}
