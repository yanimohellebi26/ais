package com.iem.backend.service;

import org.springframework.stereotype.Service;

import com.iem.backend.dto.UpdateUserRequest;
import com.iem.backend.model.User;
import com.iem.backend.repository.UserRepository;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class UserService {
    
    private final UserRepository userRepository;

    public UserService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    public User updateUser(UpdateUserRequest request, User currentUser) {
        User user = userRepository.findById(request.getId())
        .orElseThrow(() -> new RuntimeException("Utilisateur Introuvable"));

        if (request.getRole() != null && !"admin".equals(currentUser.getRole())) {
            throw new RuntimeException("Il faut être admin pour faire cela");
        }

        if (request.getRole() != null) {
            if (!List.of("user", "admin").contains(request.getRole())) {
                throw new RuntimeException("Rôle invalide");
            }
            user.setRole(request.getRole());
        }

        if (request.getPassword() != null) {

            // IMPLEMENTER UN CRYPTAGE DU MOT DE PASSE

            user.setPassword(request.getPassword());
        }

        return userRepository.save(user);
    }
 }
