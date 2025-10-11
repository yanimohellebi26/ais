package com.iem.backend.service;

import com.iem.backend.dto.UpdateUserRequest;
import com.iem.backend.entity.User;
import com.iem.backend.entity.Role;
import com.iem.backend.repository.RoleRepository;
import com.iem.backend.repository.UserRepository;
import com.iem.backend.utils.ApiLogger;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.OffsetDateTime;
import java.util.Optional;

@Service
public class UserService {

    private UserRepository userRepository;
    private ApiLogger apiLogger;
    private RoleRepository roleRepository;
    private PasswordEncoder passwordEncoder;

    public UserService(UserRepository userRepository, ApiLogger apiLogger, RoleRepository roleRepository, PasswordEncoder passwordEncoder) {
        this.userRepository = userRepository;
        this.apiLogger = apiLogger;
        this.roleRepository = roleRepository;
        this.passwordEncoder = passwordEncoder;
    }

    @Transactional
    public User updateUser(UpdateUserRequest dto) throws Exception {
        Optional<User> optionalUser = userRepository.findById(dto.getId());
        if (optionalUser.isEmpty()) {
            apiLogger.warn("User not found with id " + dto.getId());
            throw new Exception("User not found");
        }

        User user = optionalUser.get();

        if (dto.getPassword() != null && !dto.getPassword().isBlank()) {
            
            String passwordEncoded = passwordEncoder.encode(dto.getPassword());
            user.setPasswordHash(passwordEncoded);
            apiLogger.info("Password updated for user id " + dto.getId());
        }

        if (dto.getRole() != null && !dto.getRole().isBlank()) {
            Optional<Role> optionalRole = roleRepository.findByNameIgnoreCase(dto.getRole());

            if (optionalRole.isEmpty()) {
                apiLogger.warn("Role not found for " + dto.getRole());
                throw new Exception("Role not found");
            }

            Role role = optionalRole.get();
            user.setRole(role);
            apiLogger.info("Role updated for id " + dto.getId() + " with " + dto.getRole());
        }

        user.setLastUpdate(OffsetDateTime.now());

        User updatedUser = userRepository.save(user);
        apiLogger.success("User updated successfully: id " + updatedUser.getId());

        return updatedUser;
    }
}
