package com.iem.backend.service;

import com.iem.backend.dto.UpdateUserRequest;
import com.iem.backend.model.User;
import com.iem.backend.repository.UserRepository;
import com.iem.backend.utils.ApiLogger;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Optional;

@Service
public class UserService {

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private ApiLogger apiLogger;

    @Autowired
    private PasswordEncoder passwordEncoder;

    @Transactional
    public User updateUser(UpdateUserRequest dto) throws Exception {
        Optional<User> optionalUser = userRepository.findById(dto.getId());
        if (optionalUser.isEmpty()) {
            apiLogger.warn("User not found with id " + dto.getId());
            throw new Exception("User not found");
        }

        User user = optionalUser.get();

        if (dto.getPassword() != null && !dto.getPassword().isEmpty()) {
            
            String passwordEncoded = passwordEncoder.encode(dto.getPassword());
            user.setPasswordHash(passwordEncoded);
            apiLogger.info("Password updated for user id " + dto.getId());
        }

        if (dto.getStatus() != null && !dto.getStatus().isEmpty()) {
            user.setStatus(dto.getStatus());
            apiLogger.info("Status updated for user id " + dto.getId() + " to " + dto.getStatus());
        }

        User updatedUser = userRepository.save(user);
        apiLogger.success("User updated successfully: id " + updatedUser.getId());

        return updatedUser;
    }
}
