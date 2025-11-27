package com.iem.backend.service;

import com.iem.backend.dto.user.UpdateUserPasswordRequest;
import com.iem.backend.dto.user.UpdateUserRequest;
import com.iem.backend.dto.user.UserResponse;
import com.iem.backend.entity.CustomUserDetails;
import com.iem.backend.entity.User;
import com.iem.backend.entity.Role;
import com.iem.backend.exception.ApiExceptions;
import com.iem.backend.mapper.UserMapper;
import com.iem.backend.repository.RoleRepository;
import com.iem.backend.repository.UserRepository;

import lombok.extern.slf4j.Slf4j;

import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;

import java.time.OffsetDateTime;
import java.util.List;

@Service
@Slf4j
public class UserService implements UserDetailsService {

    private final UserRepository userRepository;
    private final RoleRepository roleRepository;
    private final PasswordEncoder passwordEncoder;
    private final UserMapper userMapper;

    public UserService(UserRepository userRepository, RoleRepository roleRepository, PasswordEncoder passwordEncoder, UserMapper userMapper) {
        this.userRepository = userRepository;
        this.roleRepository = roleRepository;
        this.passwordEncoder = passwordEncoder;
        this.userMapper = userMapper;
    }

    @Transactional
    public UserResponse updateUser(UpdateUserRequest request) {
        User user = userRepository.findById(request.id())
            .orElseThrow(() -> new ApiExceptions.NotFoundException("User not found"));

        if (request.password() != null && !request.password().isBlank()) {
            String passwordEncoded = passwordEncoder.encode(request.password());
            user.setPasswordHash(passwordEncoded);
        }

        if (request.role() != null && !request.role().isBlank()) {
            Role role = roleRepository.findByNameIgnoreCase(request.role())
                .orElseThrow(() -> new ApiExceptions.NotFoundException("Role not found"));
            user.setRole(role);
        }

        user.setLastUpdate(OffsetDateTime.now());

        User updatedUser = userRepository.save(user);

        return userMapper.toResponse(updatedUser);
    }

    @Transactional
    public void deleteUserById(Integer id) {
        User user = userRepository.findById(id)
                .orElseThrow(() -> new ApiExceptions.NotFoundException("User not found"));
        userRepository.delete(user);
    }
    
    @Transactional(readOnly = true)
    public List<UserResponse> getAllUsers() {
        List<User> users = userRepository.findAll();
        return userMapper.toResponseList(users);
    }

    @Override
    public UserDetails loadUserByUsername(String email) {
        User user = userRepository.findByEmailIgnoreCase(email)
                .orElseThrow(() -> new UsernameNotFoundException("User Not Found with email: " + email));
        return new CustomUserDetails(user);
    }

    @Transactional
    public UserResponse getUserById(Integer id, CustomUserDetails currentUser) {
        boolean isSelf = currentUser.getUser().getId().equals(id);
        boolean isAdmin = "ADMIN".equalsIgnoreCase(currentUser.getUser().getRole().getName());

        if(!isAdmin && !isSelf){
            throw new ApiExceptions.UnauthorizedException("You are not allowed to see this account");
        }

        return userMapper.toResponse(currentUser.getUser());
    }

    @Transactional
    public void updatePassword(Integer id, UpdateUserPasswordRequest request, CustomUserDetails currentUser) {
        User user = userRepository.findById(id)
                .orElseThrow(() -> new ApiExceptions.NotFoundException("User not found"));

        String currentUserEmail = currentUser.getUsername();
        if (!currentUserEmail.equalsIgnoreCase(user.getEmail())){
            throw new ApiExceptions.UnauthorizedException("You are not allowed to change this password");
        }

        if (!passwordEncoder.matches(request.oldPassword(), user.getPasswordHash())) {
            throw new ApiExceptions.UnauthorizedException("Old pasword is incorrect");
        }

        String newEncodedPassword = passwordEncoder.encode(request.newPassword());
        user.setPasswordHash(newEncodedPassword);
        user.setLastUpdate(OffsetDateTime.now());

        userRepository.save(user);
    }

}
