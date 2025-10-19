package com.iem.backend.service;

import com.iem.backend.dto.UpdatePasswordRequest;
import com.iem.backend.dto.UpdateUserRequest;
import com.iem.backend.dto.UserDTO;
import com.iem.backend.entity.User;
import com.iem.backend.exception.RoleNotFoundException;
import com.iem.backend.exception.UserNotFoundException;
import com.iem.backend.entity.Role;
import com.iem.backend.exception.UserAccessDeniedException;
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
import java.security.Principal;
import java.time.OffsetDateTime;

import java.util.Collections;
import java.util.List;

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
    public UserDTO updateUser(UpdateUserRequest dto) {
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

        return new UserDTO(
            updatedUser.getId(),
            updatedUser.getUsername(),
            updatedUser.getEmail(),
            updatedUser.getRole().getName(),
            null,
            updatedUser.getLastUpdate(),
            null
        );
    }

    @Transactional
    public UserDTO deleteUserById(Integer id) {
        User user = userRepository.findById(id)
            .orElseThrow(() -> {
                apiLogger.warn("Attempt to delete user with id " + id + " but was not found");
                return new UserNotFoundException(id);
            });

        userRepository.delete(user);
        apiLogger.success("User with id "+ id + " deleted successfuly");

        return new UserDTO(
            user.getId(),
            user.getUsername(),
            user.getEmail(),
            user.getRole().getName(),
            null,
            null,
            OffsetDateTime.now()
        );
    }
    
    @Transactional(readOnly = true)
    public List<UserDTO> getAllUsers() {
        List<User> users = userRepository.findAll();

        apiLogger.info("Retrieved " + users.size() + " users from the database.");

        return users.stream()
            .map(user -> new UserDTO(
                user.getId(),
                user.getUsername(),
                user.getEmail(),
                user.getRole().getName(),
                user.getCreatedAt(),
                user.getLastUpdate(),
                null
            ))
            .toList();
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

    @Transactional
    public UserDTO getUserById(int id, Principal principal){
        User user = userRepository.findById(id)
            .orElseThrow(() -> {
                apiLogger.warn("User not found with id " + id);
                return new UserNotFoundException(id);
            });

        String CurrentUserEmail = principal.getName();
        User CurrentUser = userRepository.findByEmailIgnoreCase(CurrentUserEmail)
            .orElseThrow(()-> new UserNotFoundException("user not found with "+CurrentUserEmail));
        
        boolean isSelf = CurrentUser.getId().equals(id);
        boolean isAdmin = "ADMIN".equalsIgnoreCase(CurrentUser.getRole().getName());

        if(!isAdmin && !isSelf){
            throw new UserAccessDeniedException("You are not allowed to see this account ");
        }

        return new UserDTO(
            user.getId(),
            user.getUsername(),
            user.getEmail(),
            user.getRole().getName(),
            null,
            null,
            OffsetDateTime.now()
        );
    }

    @Transactional
    public void updatePassword(int id, UpdatePasswordRequest dto, Principal principal){
        User user = userRepository.findById(id)
            .orElseThrow(() -> {
                apiLogger.warn("User not found with id " + id);
                return new UserNotFoundException(id);
            });

        String CurrentUserEmail = principal.getName();
        if (!CurrentUserEmail.equalsIgnoreCase(user.getEmail())){
            throw new UserAccessDeniedException("You are not allowed to change this password");
        }

        if (!passwordEncoder.matches(dto.oldPassword(), user.getPasswordHash())){
            throw new UserAccessDeniedException("Old pasword is incorrect");
        }

        String newEcodedPassword = passwordEncoder.encode(dto.newPassword());
        user.setPasswordHash(newEcodedPassword);
        user.setLastUpdate(OffsetDateTime.now());
        userRepository.save(user); //save en db
    }




}
