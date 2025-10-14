package com.iem.backend.service;

import com.iem.backend.dto.DeleteUserResponse;
import com.iem.backend.dto.UpdateUserRequest;
import com.iem.backend.dto.UpdateUserResponse;
import com.iem.backend.entity.User;
import com.iem.backend.exception.RoleNotFoundException;
import com.iem.backend.exception.UserNotFoundException;
import com.iem.backend.entity.Role;
import com.iem.backend.repository.RoleRepository;
import com.iem.backend.repository.UserRepository;
import com.iem.backend.utils.ApiLogger;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;

import java.time.OffsetDateTime;

import java.util.Collections;

@Service
public class UserService implements UserDetailsService {

    private final UserRepository userRepository;
    private final ApiLogger apiLogger;
    private final RoleRepository roleRepository;
    private final PasswordEncoder passwordEncoder;

    /**
     * Initializes the service with the user account repository.
     *
     * @param userRepository repository for accessing user data
     * @param apiLogger used for logs
     * @param roleRepository repository for accessing role data
     * @param passwordEncoder user for encoding password
     */
    public UserService(UserRepository userRepository, ApiLogger apiLogger, RoleRepository roleRepository, PasswordEncoder passwordEncoder) {
        this.userRepository = userRepository;
        this.apiLogger = apiLogger;
        this.roleRepository = roleRepository;
        this.passwordEncoder = passwordEncoder;
    }

    @Transactional
    public UpdateUserResponse updateUser(UpdateUserRequest dto) {
        User user = userRepository.findById(dto.id())
            .orElseThrow(() -> {
                apiLogger.warn("User not found with id " + dto.id());
                return new UserNotFoundException(dto.id());
            });

        if (dto.password() != null && !dto.password().isBlank()) {
            String passwordEncoded = passwordEncoder.encode(dto.password());
            user.setPasswordHash(passwordEncoded);
            apiLogger.info("Password updated for user id " + dto.id());
        }

        if (dto.role() != null && !dto.role().isBlank()) {
            Role role = roleRepository.findByNameIgnoreCase(dto.role())
                .orElseThrow(() -> {
                    apiLogger.warn("Role not found for " + dto.role());
                    return new RoleNotFoundException(dto.role());
                });

            user.setRole(role);
            apiLogger.info("Role updated for id " + dto.id() + " with " + dto.role());
        }

        user.setLastUpdate(OffsetDateTime.now());

        User updatedUser = userRepository.save(user);
        apiLogger.success("User updated successfully: id " + updatedUser.getId());

        return new UpdateUserResponse(
            updatedUser.getId(),
            updatedUser.getEmail(),
            updatedUser.getRole().getName(),
            updatedUser.getLastUpdate()
        );
    }

    @Transactional
    public DeleteUserResponse deleteUserById(Integer id) {
        User user = userRepository.findById(id)
            .orElseThrow(() -> {
                apiLogger.warn("Attempt to delete user with id " + id + " but was not found");
                return new UserNotFoundException(id);
            });

        userRepository.delete(user);
        apiLogger.success("User with id "+ id + " deleted successfuly");

        return new DeleteUserResponse(
            user.getId(),
            user.getUsername(),
            user.getEmail(),
            user.getRole().getName(),
            OffsetDateTime.now()
        );
    }

    /**
     * Loads a user by their email address for authentication.
     *
     * @param email user's email
     * @return user details for authentication
     * @throws UsernameNotFoundException if no user is found with the given email
     */
    @Override
    public UserDetails loadUserByUsername(String email) {
        User user = userRepository.findByEmailIgnoreCase(email)
                .orElseThrow(() -> new UsernameNotFoundException("User Not Found with email: " + email));

        var authority = new SimpleGrantedAuthority("ROLE_" + user.getRole().getName());

        return new org.springframework.security.core.userdetails.User(
                user.getEmail(),
                user.getPasswordHash(),
                Collections.singletonList(authority)
        );
    }

}
